# Agent Design Document

## 1. Purpose

The Voyon Attendance Agent is an AI-powered natural-language interface for the
Voyon Folks HRMS platform. It allows HR managers and employees to query
attendance data using plain English, without navigating complex reports or
dashboards.

## 2. LangGraph Workflow Design

### 2.1 State Schema (`AttendanceAgentState`)

```python
class AttendanceAgentState(TypedDict):
    messages:              Annotated[List[BaseMessage], add_messages]
    intent:                Optional[str]
    parameters:            Optional[Dict[str, Any]]
    selected_tools:        Optional[List[str]]
    tool_results:          Optional[Dict[str, Any]]
    last_employee_id:      Optional[int]
    last_employee_name:    Optional[str]
    final_response:        Optional[str]
    error:                 Optional[str]
```

Key design choices:
- `add_messages` reducer automatically appends messages (no overwrites)
- Auth info (JWT token, employee_id, full_name) is passed via **LangGraph `configurable`**,
  not stored in state, so it never appears in checkpointer snapshots
- Each chat turn resets `final_response` and `tool_results` in `run_agent()` so prior turn state is not reused
- `last_employee_id` / `last_employee_name` persist across turns for follow-up queries (e.g. "show her history")

### 2.2 Node Descriptions

#### `intent_detection_node`
- Sends a single LLM call with a classification prompt
- Returns one of:
  `present_query | absent_query | summary_query | history_query |
   employee_detail | search_employee | my_attendance |
   unclear | out_of_scope`
- No tools bound — pure classification

#### `parameter_extraction_node`
- Sends a structured extraction prompt asking for date, month, year,
  employee_name, employee_id, reporting_type
- Includes **recent conversation context** and last-discussed employee
- Returns parsed JSON; falls back to empty dict on parse error
- Normalises relative dates ("today", "yesterday") to ISO format

#### `context_enrichment_node`
- Fills missing `employee_name` / `employee_id` when the user says "her", "him", etc.
- Updates `last_employee_id` / `last_employee_name` for the session thread
- Runs after parameter extraction, before tool selection

#### `tool_selection_node`
- Pure Python — no LLM call
- Maps intent → tool name list (see table below)

| Intent | Selected tools |
|--------|----------------|
| `present_query` | `get_present_employees` |
| `absent_query` | `get_absent_employees` |
| `summary_query` | `get_attendance_summary` |
| `history_query` | `get_attendance_history` |
| `employee_detail` | `search_employee`, `get_employee_attendance_details` |
| `search_employee` | `search_employee` |
| `my_attendance` | `get_my_attendance_today` |
| `unclear` / `out_of_scope` | _(none)_ |

#### `direct_tool_execution_node`
- Executes intent-mapped tools **without LLM tool selection**
- Used for `DIRECT_TOOL_INTENTS`: `summary_query`, `present_query`, `absent_query`, `my_attendance`
- Injects synthetic `AIMessage` + `ToolMessage` pairs into state, then routes to `response_generation`
- Ensures reliable tool choice for high-frequency queries (e.g. "attendance summary for today")

#### `agent_node`
- Core ReAct node: `AzureChatOpenAI.bind_tools(ATTENDANCE_TOOLS)`
- Loads system prompt from `systemprompt.txt` via `prompt_loader.py`
- Prepends system message with user identity (`full_name`, `employee_id`) and today's date
- Injects intent-based routing hints on the first turn (no tool results yet)
- Calls `_sanitize_messages()` to remove orphaned tool calls from persisted history
- Emits tool calls or a final text response

#### `tool_executor`
- `langgraph.prebuilt.ToolNode(ATTENDANCE_TOOLS)`
- Automatically passes `RunnableConfig` (including JWT token) to each tool

#### `response_generation_node`
- Builds the final user-facing response from **this turn's** messages only (`_current_turn_messages`)
- Extracts the last non-tool-call AI message, or falls back to an LLM summarisation call

### 2.3 Graph Edges

```
START → intent_detection
intent_detection → parameter_extraction
parameter_extraction → context_enrichment
context_enrichment → tool_selection
tool_selection → (DIRECT_TOOL_INTENTS?) direct_tools
              → agent
direct_tools → response_generation
agent → (tool_calls?) tools : response_generation
tools → agent      [ReAct loop]
response_generation → END
```

## 3. Tool Design

All seven tools are defined in `src/agent/tools.py` and exported as `ATTENDANCE_TOOLS`.

### Tool: `get_present_employees`
- **API**: `GET /m/api/Attendance/team-attendance`
- **Filters**: `_emp_status()` == `"Present"`
- **Parameters**: `date_str` (YYYY-MM-DD), `reporting_type` (0/1/2)
- **Auth**: JWT from `config["configurable"]["jwt_token"]`

### Tool: `get_absent_employees`
- **API**: Same `team-attendance` endpoint
- **Filters**: status NOT IN (Present, Holiday, WeeklyOff)

### Tool: `get_attendance_summary`
- **API**: Same `team-attendance` endpoint
- **Output**: Uses `_extract_summary_counts()` when available; otherwise counts via `_emp_status()`
- **Direct execution**: Yes (via `direct_tools` node)

### Tool: `get_attendance_history`
- **Primary API**: `GET /m/api/Attendance/MonthlyAttendance`
- **Fallback API**: `GET /m/api/Attendance/AttendanceBasedOnDate` (day-by-day for each day in month)
- **Parameters**: `month`, `year`, `employee_id`, `employee_name`
- **Name resolution**: If only `employee_name` is given, calls mobile search API first;
  uses `_extract_numeric_id()` to safely parse `EmployeeId` (ignores string employee codes in `Id`)
- **Fallback summary**: When using day-by-day fallback, computes `summary` counts
  (present, absent, leave, holiday, weekoff, total_days) from daily `Status` / `DayType` fields
- **Defaults**: Uses session `employee_id` when no target employee specified

### Tool: `search_employee`
- **Primary API**: `GET /m/api/Employee/search-employees/{searchValue}/{page}`
- **Fallback API**: `GET /m/api/Attendance/team-attendance` (client-side name/code/ID filter)
- **Parameters**: `query`, optional `date_str` for fallback

### Tool: `get_my_attendance_today`
- **API**: `GET /m/api/Attendance/AttendanceBasedOnDate`
- **Always uses session employee_id** — never takes it from the model
- **Direct execution**: Yes (via `direct_tools` node)

### Tool: `get_employee_attendance_details`
- **Primary API**: `GET /m/api/Attendance/AttendanceBasedOnDate`
- **Fallback API**: `GET /m/api/Attendance/team-attendance` (find employee in team list)
- **Profile lookup**: `GET /m/api/Employee/GetEmployeeDetails` for display name
- **Parameters**: `employee_id` (required), `date_str` (defaults to today)
- **Typical flow**: `search_employee` first when user provides a name, then this tool with resolved ID

## 4. Prompt Design

### System Prompt (`systemprompt.txt`)
Loaded at startup by `src/agent/prompt_loader.py` and formatted with:
- `{full_name}` — authenticated user's display name
- `{employee_id}` — authenticated user's numeric ID
- `{today}` — current ISO date

Key sections:
1. **Role and scope** — attendance-only assistant
2. **Tool usage rules** — when to use each of the 7 tools
3. **Response style** — markdown tables; monthly history must include summary counts

### Why multiple LLM calls per turn?
- Turn 1: Intent classification (small, fast)
- Turn 2: Parameter extraction (structured JSON output)
- Turn 3+: ReAct loop (tool calls + final response) — skipped for direct-tool intents

This separation gives better accuracy and debuggability than a single monolithic prompt.

## 5. Error Handling

| Scenario | Behaviour |
|----------|-----------|
| HRMS API 401 | `HrmsApiError` — session expired; user redirected to login |
| HRMS API 4xx/5xx | Tool returns `{"error": "..."}` string; LLM generates apologetic response |
| MonthlyAttendance 500 | `get_attendance_history` falls back to day-by-day `AttendanceBasedOnDate` |
| Invalid employee ID in search | `_extract_numeric_id()` skips string codes; returns user-friendly error |
| Network timeout | `httpx` timeout after 30s; generic error response |
| LLM classification error | Invalid intent → `unclear`; LLM asks for clarification |
| JSON parse error (extraction) | Falls back to empty params dict |
| Orphaned tool calls in history | `_sanitize_messages()` drops incomplete tool-call pairs before LLM invoke |
| Graph exception | Router catches, returns generic error message |

## 6. Session Management

- Server-side sessions stored in a Python `dict` (production: Redis)
- Session ID signed with `itsdangerous.URLSafeSerializer`
- Cookie: `attend_session` — HttpOnly, SameSite=Lax
- LangGraph uses `session_id` as `thread_id` for `MemorySaver`
- Conversation history is maintained across turns in the same session

## 7. Security Considerations

1. **Token isolation**: JWT token is never exposed to client JS or LLM responses
2. **Employee ID pinning**: Session-scoped tools use session `employee_id`; LLM cannot escalate
3. **Tool allowlist**: Only the 7 defined tools in `ATTENDANCE_TOOLS` can be invoked
4. **Signed cookies**: Session IDs cannot be forged without server secret
5. **SSL**: Production deployment should use HTTPS; `HRMS_SSL_VERIFY=true`
