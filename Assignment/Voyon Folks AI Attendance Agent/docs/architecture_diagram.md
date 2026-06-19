# Architecture Diagram — Voyon Attendance Agent

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VOYON ATTENDANCE AGENT                              │
│                                                                             │
│  ┌──────────────────────┐        ┌──────────────────────────────────────┐  │
│  │    Browser (HTML/JS) │◄──────►│         FastAPI Backend               │  │
│  │                      │  HTTP  │  ┌──────────┐   ┌──────────────────┐ │  │
│  │  login.html          │        │  │auth_router│   │  chat_router     │ │  │
│  │  index.html          │        │  │ /login    │   │  POST /api/chat  │ │  │
│  │  (Jinja2 templates)  │        │  │ /logout   │   │  POST /api/chat  │ │  │
│  └──────────────────────┘        │  └──────────┘   └────────┬─────────┘ │  │
│                                  └───────────────────────────┼───────────┘  │
│                                                              │               │
│                                                              ▼               │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    LANGGRAPH AGENT WORKFLOW                           │  │
│  │                                                                       │  │
│  │   START                                                               │  │
│  │     │                                                                 │  │
│  │     ▼                                                                 │  │
│  │  [intent_detection]  ─── classify: present/absent/summary/history    │  │
│  │     │                  employee_detail/search/unclear/out_of_scope    │  │
│  │     ▼                                                                 │  │
│  │  [parameter_extraction] ─── extract: date, employee, month, year     │  │
│  │     │                                                                 │  │
│  │     ▼                                                                 │  │
│  │  [tool_selection] ─── map intent → tools                             │  │
│  │     │                                                                 │  │
│  │     ├── (summary/present/absent/my_attendance)                       │  │
│  │     │         ──► [direct_tools] ──► [response_generation] ──► END  │  │
│  │     │                                                                 │  │
│  │     └──────────────────────► [agent_node] ◄─────────────────────┐   │  │
│  │                                   │                              │   │  │
│  │                              tool_calls?                         │   │  │
│  │                               ├── YES ──► [tool_executor] ───────┘   │  │
│  │                               └── NO                                  │  │
│  │                                    │                                  │  │
│  │                                    ▼                                  │  │
│  │                          [response_generation]                        │  │
│  │                                    │                                  │  │
│  │                                   END                                 │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│                         ▼  LangGraph Tools (7 tools)                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  get_present_employees()      get_absent_employees()                  │  │
│  │  get_attendance_summary()     get_attendance_history()                  │  │
│  │  search_employee()            get_my_attendance_today()                 │  │
│  │  get_employee_attendance_details()                                      │  │
│  └────────────────────────────────┬──────────────────────────────────────┘  │
│                                   │ HTTP (JWT Bearer)                        │
└───────────────────────────────────┼─────────────────────────────────────────┘
                                    │
                    ┌───────────────▼──────────────────┐
                    │   Voyon Folks HRMS Web App        │
                    │   (HRMS_BASE_URL)                 │
                    │                                   │
                    │  POST /m/api/Login/LoginUser      │
                    │  GET  /m/api/Attendance/          │
                    │       team-attendance             │
                    │  GET  /m/api/Attendance/          │
                    │       AttendanceBasedOnDate       │
                    │  GET  /m/api/Attendance/          │
                    │       MonthlyAttendance           │
                    │  GET  /m/api/Employee/            │
                    │       search-employees/{q}/{page} │
                    │  GET  /m/api/Employee/            │
                    │       GetEmployeeDetails          │
                    └───────────────────────────────────┘
```

## Component Descriptions

| Component | Technology | Responsibility |
|-----------|-----------|----------------|
| **Browser UI** | HTML5 / CSS3 / Vanilla JS | Chat interface, login, quick action buttons |
| **FastAPI** | Python 3.11+ | HTTP server, session management, routing |
| **Auth Router** | itsdangerous + httpx | Login/logout, signed cookies, HRMS JWT |
| **Chat Router** | FastAPI | `/api/chat`, `/api/me` |
| **LangGraph Graph** | LangGraph 0.2+ | Orchestrates the multi-step agent workflow |
| **Intent Detection** | Azure OpenAI (LLM call) | Classifies user query type |
| **Parameter Extraction** | Azure OpenAI (LLM call) | Extracts dates, names, IDs |
| **Tool Selection** | Python logic | Maps intent → tool list |
| **direct_tools** | Python (no LLM) | Executes summary/present/absent/my_attendance tools directly |
| **agent_node** | AzureChatOpenAI + bind_tools | ReAct loop with HRMS tools |
| **tool_executor** | LangGraph ToolNode | Executes attendance tools from LLM tool calls |
| **response_generation** | Python + LLM | Formats final natural-language answer |
| **HrmsClient** | httpx async | HTTP calls to Voyon HRMS REST APIs |
| **MemorySaver** | LangGraph | Persists conversation state per thread |
| **systemprompt.txt** | Text file | External system prompt template loaded at startup |

## Data Flow — Direct Tool Path (summary / present / absent / my attendance)

```
User types: "Show attendance summary for today"
  │
  ▼
POST /api/chat {"message": "Show attendance summary for today"}
  │
  ▼
intent_detection → "summary_query"
  │
  ▼
parameter_extraction → {"date": "2026-06-19"}
  │
  ▼
tool_selection → ["get_attendance_summary"]
  │
  ▼
direct_tools → get_attendance_summary(date="2026-06-19")  [no LLM tool-picking]
  │
  ▼
GET /m/api/Attendance/team-attendance?...
  │
  ▼
response_generation → formatted summary with counts
  │
  ▼
JSON response: {"reply": "..."}
```

## Data Flow — Agent ReAct Path (history / employee detail / search)

```
User types: "Show attendance history for Greeshma this month"
  │
  ▼
intent_detection → "history_query"
  │
  ▼
parameter_extraction → {"employee_name": "Greeshma", "month": 6, "year": 2026}
  │
  ▼
tool_selection → ["get_attendance_history"]
  │
  ▼
agent_node → LLM calls get_attendance_history(employee_name="Greeshma", month=6, year=2026)
  │
  ▼
tool_executor:
  1. search-employees API → resolve numeric EmployeeId
  2. MonthlyAttendance API (primary)
     OR day-by-day AttendanceBasedOnDate fallback + summary counts
  │
  ▼
agent_node → LLM formats table + summary counts
  │
  ▼
response_generation → final reply
```

## Security Design

- All API calls use JWT Bearer token from the authenticated HRMS session
- `employee_id` for auth-scoped operations is ALWAYS taken from the server-side session — never from LLM output
- Tool allowlist prevents prompt-injection from invoking unauthorised operations
- Sessions are stored server-side; only a signed session ID is sent to the browser
- `_sanitize_messages()` strips orphaned tool-call messages before LLM requests to prevent API 400 errors
