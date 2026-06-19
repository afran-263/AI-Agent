"""LangGraph node functions for the Attendance Agent workflow.

Workflow:
    intent_detection ──► parameter_extraction ──► tool_selection
    ──► api_execution (agent ReAct loop)
    ──► response_generation
"""
from __future__ import annotations

import json
import logging
import re
from datetime import date
from typing import Any, Dict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import ToolNode

from src.config import settings
from src.agent.state import AttendanceAgentState
from src.agent.tools import (
    ATTENDANCE_TOOLS,
    try_format_employee_detail_from_turn,
    try_format_history_from_turn,
    wants_monthly_summary_style,
    try_format_list_from_turn,
    try_format_my_attendance_from_turn,
)
from src.agent.prompt_loader import load_system_prompt_template

logger = logging.getLogger(__name__)

# ── LLM singleton ─────────────────────────────────────────────────────────────
_llm = AzureChatOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    api_key=settings.azure_openai_api_key,
    azure_deployment=settings.azure_openai_deployment,
    api_version=settings.azure_openai_api_version,
    temperature=0,
    streaming=False,
)

_llm_with_tools = _llm.bind_tools(ATTENDANCE_TOOLS)

# ── ToolNode (executes tool calls emitted by the LLM) ─────────────────────────
tool_executor = ToolNode(ATTENDANCE_TOOLS)

_TOOLS_BY_NAME = {t.name: t for t in ATTENDANCE_TOOLS}

# Intents that call exactly one known tool — executed directly, no LLM tool-picking
DIRECT_TOOL_INTENTS = frozenset({
    "summary_query", "present_query", "absent_query", "my_attendance",
    "team_list_query", "history_query", "employee_detail",
})

_TEAM_LIST_FOLLOWUP_RE = re.compile(
    r"\b(all details|full list|list them all|show everyone|show all employees|"
    r"list all|get all|complete list|entire team|all employees)\b",
    re.IGNORECASE,
)
_TEAM_LIST_QUERY_RE = re.compile(
    r"\b(list of employees|list employees|employee list|show all employees|"
    r"team roster|all employees in|get the list of employees)\b",
    re.IGNORECASE,
)
_MONTHLY_SUMMARY_QUERY_RE = re.compile(
    r"\b(this month|current month|month so far|till now|until now|to date)\b.*\b(summary|overview)\b|"
    r"\b(summary|overview)\b.*\b(this month|current month|month)\b|"
    r"\battendance summary\b.*\b(month|this month)\b|"
    r"\b(month|this month)\b.*\battendance summary\b",
    re.IGNORECASE,
)
_HISTORY_QUERY_RE = re.compile(
    r"\b(history|historical|monthly)\b.*\battendance\b|"
    r"\battendance\b.*\b(history|historical|monthly)\b|"
    r"\b(last month|previous month|this month|current month)\b",
    re.IGNORECASE,
)
_EMPLOYEE_DETAIL_QUERY_RE = re.compile(
    # Must mention "detail(s)" explicitly — not summary, history, or list
    r"\battendance\s+details?\s+(for|of)\b|"
    r"\bdetails?\s+of\s+attendance\b|"
    # Check-in / check-out time questions
    r"\bwhat\s+time\s+did\b.*\bcheck[\s-]?in\b|"
    r"\b(check[\s-]?in|check[\s-]?out)\s+time\s+(for|of)\b|"
    r"\bdid\b.*\bcheck[\s-]?(in|out)\b",
    re.IGNORECASE,
)
_EMPLOYEE_DETAIL_EXCLUSION_RE = re.compile(
    r"\b(summary|history|list|roster|absent|present|who)\b",
    re.IGNORECASE,
)
_EMPLOYEE_NAME_FROM_DETAIL_RE = re.compile(
    r"\battendance\s+details?\s+for\s+([A-Za-z][A-Za-z\s'-]+?)(?:\s+today|\s+on\s+|\s+yesterday|\s*$)",
    re.IGNORECASE,
)

_EMPLOYEE_REFERENCE_RE = re.compile(
    r"\b(her|his|him|she|he|they|them|that employee|same employee|that person|"
    r"the employee|this employee)\b",
    re.IGNORECASE,
)

# ── System prompt (loaded from systemprompt.txt) ─────────────────────────────
_SYSTEM_PROMPT_TEMPLATE = load_system_prompt_template()


def build_system_message(full_name: str, employee_id: int) -> SystemMessage:
    today = date.today().isoformat()
    return SystemMessage(
        content=_SYSTEM_PROMPT_TEMPLATE.format(
            full_name=full_name,
            employee_id=employee_id,
            today=today,
        )
    )


def _current_turn_messages(messages: list) -> list:
    """Return only messages from the latest HumanMessage onward (current turn)."""
    last_human_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], HumanMessage):
            last_human_idx = i
            break
    if last_human_idx >= 0:
        return messages[last_human_idx:]
    return messages


def _sanitize_messages(messages: list) -> list:
    """
    Remove orphaned assistant tool-call messages from conversation history.

    OpenAI/Azure reject a request where an AIMessage with tool_calls is NOT
    immediately followed by ToolMessages covering every tool_call_id.  This
    happens when the user sends a new message before the previous tool round
    completes (e.g. interrupted turns, rapid successive queries).

    Strategy: walk the list; whenever we see an AIMessage with tool_calls,
    collect the tool_call_ids that follow as ToolMessages.  If any id is
    missing, drop the AIMessage and all partial ToolMessages for it.
    """
    if not messages:
        return messages

    result: list = []
    i = 0
    while i < len(messages):
        msg = messages[i]
        if isinstance(msg, AIMessage) and msg.tool_calls:
            expected_ids = {tc["id"] for tc in msg.tool_calls}
            # Gather consecutive ToolMessages that follow
            j = i + 1
            found_ids: set = set()
            while j < len(messages) and isinstance(messages[j], ToolMessage):
                found_ids.add(messages[j].tool_call_id)
                j += 1
            if expected_ids.issubset(found_ids):
                # All responses present — keep AIMessage + its ToolMessages
                result.append(msg)
                result.extend(messages[i + 1 : j])
            else:
                # Orphaned tool call — drop it (and any partial ToolMessages)
                logger.warning(
                    "_sanitize_messages: dropping orphaned tool call(s) %s",
                    expected_ids - found_ids,
                )
            i = j
        else:
            result.append(msg)
            i += 1

    return result


def _format_conversation_context(messages: list, max_exchanges: int = 3) -> str:
    """
    Build a short text summary of prior user/assistant turns (no tool payloads).
    Excludes the latest user message — that is passed separately as the current query.
    """
    lines: list[str] = []
    for msg in messages:
        if isinstance(msg, HumanMessage) and msg.content:
            lines.append(f"User: {str(msg.content).strip()[:300]}")
        elif isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            lines.append(f"Assistant: {str(msg.content).strip()[:300]}")

    if len(lines) <= 1:
        return ""

    # Drop current user message (last line if it's from the user)
    if lines[-1].startswith("User:"):
        lines = lines[:-1]

    if not lines:
        return ""

    recent = lines[-(max_exchanges * 2):]
    return "Recent conversation:\n" + "\n".join(recent)


def _has_employee_reference(text: str) -> bool:
    return bool(_EMPLOYEE_REFERENCE_RE.search(text or ""))


def _format_last_employee_context(state: AttendanceAgentState) -> str:
    name = state.get("last_employee_name")
    emp_id = state.get("last_employee_id")
    if name and emp_id:
        return f"Last discussed employee: {name} (ID: {emp_id})"
    if name:
        return f"Last discussed employee: {name}"
    if emp_id:
        return f"Last discussed employee ID: {emp_id}"
    return ""


def _extract_employee_from_tool_results(tool_results: dict | None) -> tuple[int | None, str | None]:
    """Try to pull employee id/name from search or attendance tool JSON."""
    if not tool_results:
        return None, None

    for raw in tool_results.values():
        try:
            data = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(data, dict):
            continue

        # search_employee: {"matches": [...]}
        matches = data.get("matches")
        if isinstance(matches, list) and matches:
            first = matches[0]
            if isinstance(first, dict):
                emp_id = (
                    first.get("EmployeeId") or first.get("employeeId") or first.get("Id")
                )
                name = (
                    first.get("EmployeeName") or first.get("employeeName") or
                    first.get("FullName") or first.get("fullName") or first.get("Name")
                )
                try:
                    return int(emp_id), str(name) if name else None
                except (TypeError, ValueError):
                    pass

        # attendance tools: top-level employee fields
        emp_id = data.get("employee_id") or data.get("EmployeeId")
        name = data.get("employee_name") or data.get("EmployeeName")
        try:
            if emp_id:
                return int(emp_id), str(name) if name else None
        except (TypeError, ValueError):
            pass

    return None, None


# ── Node: intent detection ────────────────────────────────────────────────────

def intent_detection_node(state: AttendanceAgentState) -> Dict[str, Any]:
    """
    Classify the user's intent from the latest human message.
    This node uses a simple LLM call (no tools) to quickly classify the query.
    """
    messages = state["messages"]
    if not messages:
        return {"intent": "unclear"}

    last_human = next(
        (m.content for m in reversed(messages) if isinstance(m, HumanMessage)),
        ""
    )
    prior_context = _format_conversation_context(messages)
    last_employee_ctx = _format_last_employee_context(state)

    context_block = ""
    if prior_context:
        context_block += f"\n{prior_context}\n"
    if last_employee_ctx:
        context_block += f"{last_employee_ctx}\n"

    classification_prompt = f"""\
Classify the user's attendance-related query into exactly one of these intents:
- present_query: asking who is present / at work
- absent_query: asking who is absent / not present
- summary_query: asking for an overview or count of attendance statuses for a **single day** (team summary today, how many present/absent today) — counts only, NOT a name list, NOT monthly
- team_list_query: asking for a full list/roster of ALL team employees (with ID and name), e.g. "list of employees", "show all employees", "get all details", "full list"
- history_query: asking for historical or monthly attendance (this month, month-to-date summary, date range, attendance history)
- employee_detail: asking for a specific named employee's attendance details on a date (check-in, check-out, worked hours, shift)
- search_employee: looking up an employee by name or ID only (no attendance data needed)
- my_attendance: asking ONLY about their own personal attendance today (my check-in, my status)
- unclear: the query is ambiguous and needs clarification
- out_of_scope: the query is not about attendance at all

Use the recent conversation when the current message is a follow-up (e.g. "what about yesterday?", "show her history").

Examples:
- "What time did John check in today?" → employee_detail
- "Show attendance for Sarah on Monday" → employee_detail
- "Show attendance details for Kanchana today" → employee_detail
- "Find employee named Riya" → search_employee
- "Who is absent today?" → absent_query
- "Who is present today?" → present_query
- "Show attendance summary for today" → summary_query
- "How many employees are there?" → summary_query
- "Show my attendance summary for this month" → history_query
- "Attendance summary for this month till now" → history_query
- "How many days was I present this month?" → history_query
- "Get the list of employees" → team_list_query
- "Show all employees in my team" → team_list_query
- (after team count/summary) "get all details" / "show full list" → team_list_query
- "What is my attendance today?" → my_attendance
- "Did I check in?" → my_attendance
- (after discussing Greeshma) "Show her history this month" → history_query
- (after discussing team attendance) "What about yesterday?" → same category as prior question

{context_block}
Current user query: "{last_human}"

Reply with just the intent label. Nothing else."""

    response = _llm.invoke([HumanMessage(content=classification_prompt)])
    intent = response.content.strip().lower().replace(" ", "_")

    # Guard against unexpected values
    valid_intents = {
        "present_query", "absent_query", "summary_query", "team_list_query",
        "history_query", "employee_detail", "search_employee", "my_attendance",
        "unclear", "out_of_scope",
    }
    if intent not in valid_intents:
        intent = "unclear"

    logger.info("Intent detected: %s", intent)
    return {"intent": intent}


# ── Node: parameter extraction ────────────────────────────────────────────────

def parameter_extraction_node(state: AttendanceAgentState) -> Dict[str, Any]:
    """
    Extract structured parameters (date, employee name/ID, month, year)
    from the conversation. Returns them in a typed dict.
    """
    messages = state["messages"]
    last_human = next(
        (m.content for m in reversed(messages) if isinstance(m, HumanMessage)),
        ""
    )
    intent = state.get("intent", "unclear")
    today = date.today().isoformat()
    prior_context = _format_conversation_context(messages)
    last_employee_ctx = _format_last_employee_context(state)

    context_block = ""
    if prior_context:
        context_block += f"\n{prior_context}\n"
    if last_employee_ctx:
        context_block += f"{last_employee_ctx}\n"

    extraction_prompt = f"""\
Extract parameters from the user query for an attendance query of type "{intent}".

{context_block}
Current user query: "{last_human}"
Today's date: {today}

Return a JSON object with these fields (use null for missing values):
{{
  "date": "<YYYY-MM-DD or null>",
  "month": <1-12 or null>,
  "year": <4-digit year or null>,
  "employee_name": "<name or null>",
  "employee_id": <integer or null>,
  "reporting_type": <0=all, 1=direct, 2=indirect — default 0>
}}

Rules:
- If the user says "today", set date to {today}.
- If the user says "yesterday", set date to the correct date.
- If month/year are mentioned for history, set those fields.
- For follow-ups ("her history", "what about last month"), resolve employee/date from recent conversation and last discussed employee.
- For absent_query, present_query, or summary_query, leave month and year as null unless explicitly mentioned.
- IMPORTANT: If the query contains only first-person words like "my", "mine", "I", "me" (not a real name), set employee_name to null. "My attendance" means the logged-in user, not an employee named "my".
- Only output the JSON object. No other text."""

    response = _llm.invoke([HumanMessage(content=extraction_prompt)])
    try:
        params = json.loads(response.content.strip())
    except (json.JSONDecodeError, ValueError):
        params = {}

    logger.info("Parameters extracted: %s", params)
    return {"parameters": params}


# ── Node: context enrichment (resolve follow-ups from prior turns) ─────────────

def context_enrichment_node(state: AttendanceAgentState) -> Dict[str, Any]:
    """
    Fill missing employee parameters from session memory and update last-discussed employee.
    """
    params = dict(state.get("parameters") or {})
    messages = state.get("messages") or []
    last_human = next(
        (m.content for m in reversed(messages) if isinstance(m, HumanMessage)),
        "",
    )

    last_name = state.get("last_employee_name")
    last_id = state.get("last_employee_id")

    # Resolve pronouns / vague references using persisted employee context
    if _has_employee_reference(str(last_human)):
        if not params.get("employee_name") and not params.get("employee_id"):
            if last_name:
                params["employee_name"] = last_name
                logger.info("context_enrichment: resolved reference → employee_name=%s", last_name)
            elif last_id:
                params["employee_id"] = last_id
                logger.info("context_enrichment: resolved reference → employee_id=%s", last_id)

    # Strip pronoun "employee names" the LLM may have hallucinated
    _SELF_PRONOUNS = {"my", "mine", "i", "me", "myself", "our", "we"}
    if str(params.get("employee_name") or "").strip().lower() in _SELF_PRONOUNS:
        params["employee_name"] = None
        logger.info("context_enrichment: cleared pronoun employee_name")

    updates: Dict[str, Any] = {"parameters": params}

    # Phrase-based intent overrides only refine attendance queries — never
    # reroute an out-of-scope query (e.g. "my salary this month") into an
    # attendance intent.
    if state.get("intent") == "out_of_scope":
        return updates

    # Direct phrases → full team roster (ID + name for everyone)
    if _TEAM_LIST_QUERY_RE.search(str(last_human)):
        updates["intent"] = "team_list_query"
        logger.info("context_enrichment: phrase match → team_list_query")

    # Month-to-date summary or plain history → history_query
    elif _MONTHLY_SUMMARY_QUERY_RE.search(str(last_human)) or _HISTORY_QUERY_RE.search(str(last_human)):
        today = date.today()
        if _MONTHLY_SUMMARY_QUERY_RE.search(str(last_human)) or re.search(
            r"\b(this month|current month)\b", str(last_human), re.IGNORECASE
        ):
            if not params.get("month"):
                params["month"] = today.month
            if not params.get("year"):
                params["year"] = today.year
        updates["parameters"] = params
        updates["intent"] = "history_query"
        logger.info(
            "context_enrichment: history/summary phrase → history_query (month=%s year=%s)",
            params.get("month"), params.get("year"),
        )

    # Named employee attendance details (check-in/out) — not summary, history, or roster
    elif (
        _EMPLOYEE_DETAIL_QUERY_RE.search(str(last_human))
        and not _EMPLOYEE_DETAIL_EXCLUSION_RE.search(str(last_human))
    ):
        if not params.get("employee_name"):
            name_match = _EMPLOYEE_NAME_FROM_DETAIL_RE.search(str(last_human))
            if name_match:
                params["employee_name"] = name_match.group(1).strip()
        if not params.get("date") and re.search(r"\btoday\b", str(last_human), re.IGNORECASE):
            params["date"] = date.today().isoformat()
        updates["parameters"] = params
        updates["intent"] = "employee_detail"
        logger.info("context_enrichment: phrase match → employee_detail")

    # Follow-up: user wants full team roster after a count/summary discussion
    elif _TEAM_LIST_FOLLOWUP_RE.search(str(last_human)):
        prior = _format_conversation_context(messages).lower()
        if any(kw in prior for kw in ("employee", "team", "summary", "present", "absent", "attendance")):
            updates["intent"] = "team_list_query"
            logger.info("context_enrichment: follow-up → team_list_query")

    if params.get("employee_name"):
        updates["last_employee_name"] = str(params["employee_name"]).strip()
    if params.get("employee_id"):
        try:
            updates["last_employee_id"] = int(params["employee_id"])
        except (TypeError, ValueError):
            pass

    return updates


# ── Node: tool selection ──────────────────────────────────────────────────────

def tool_selection_node(state: AttendanceAgentState) -> Dict[str, Any]:
    """Map the detected intent to which tools should be called."""
    intent = state.get("intent", "unclear")
    params = state.get("parameters") or {}

    intent_to_tools = {
        "present_query":   ["get_present_employees"],
        "absent_query":    ["get_absent_employees"],
        "team_list_query": ["get_team_employee_list"],
        "summary_query":   ["get_attendance_summary"],
        "history_query":   ["get_attendance_history"],
        "employee_detail": ["get_employee_attendance_details"],
        "search_employee": ["search_employee"],
        "my_attendance":   ["get_my_attendance_today"],
        "unclear":         [],
        "out_of_scope":    [],
    }

    selected = intent_to_tools.get(intent, [])

    return {
        "selected_tools": selected,
    }


def _build_tool_routing_hint(state: AttendanceAgentState) -> str | None:
    """Tell the LLM which tool(s) to call based on detected intent."""
    selected = state.get("selected_tools") or []
    if not selected:
        return None

    intent = state.get("intent", "unclear")
    params = state.get("parameters") or {}
    tools = ", ".join(f"`{name}`" for name in selected)
    hint = f"Detected intent: {intent}. You MUST call: {tools}."

    if intent == "summary_query":
        hint += (
            " Do NOT call `get_my_attendance_today` — it returns only the logged-in user."
            " Use `get_attendance_summary` for team counts and status breakdown."
        )
    elif intent == "my_attendance":
        hint += " Do NOT call `get_attendance_summary`. Use `get_my_attendance_today` only."
    elif intent == "history_query":
        emp_name = params.get("employee_name")
        emp_id = params.get("employee_id")
        if emp_name and not emp_id:
            hint += (
                f" The user wants history for employee named '{emp_name}'."
                f" Call `get_attendance_history` with `employee_name='{emp_name}'`"
                " — the tool will automatically resolve the name to an employee ID."
            )
        elif emp_id:
            hint += (
                f" The user wants history for employee_id={emp_id}."
                f" Call `get_attendance_history` with `employee_id={emp_id}`."
            )
        elif not emp_id:
            hint += (
                " No employee was specified — call `get_attendance_history`"
                " without an employee_id to return the logged-in user's own history."
            )
    elif intent == "employee_detail":
        emp_name = params.get("employee_name")
        emp_id = params.get("employee_id")
        target_date = params.get("date") or date.today().isoformat()
        if emp_name and not emp_id:
            hint += (
                f" Call `get_employee_attendance_details` with `employee_name='{emp_name}'`"
                f" and `date_str='{target_date}'`. Do NOT call `search_employee`."
            )
        elif emp_id:
            hint += (
                f" Call `get_employee_attendance_details` with `employee_id={emp_id}`"
                f" and `date_str='{target_date}'`."
            )
        else:
            hint += (
                f" Call `get_employee_attendance_details` with `date_str='{target_date}'`"
                " once you know which employee the user means."
            )

    return hint


def _build_tool_args(tool_name: str, params: dict) -> dict:
    """Map extracted parameters to tool argument names."""
    args: dict = {}
    if tool_name in (
        "get_attendance_summary",
        "get_present_employees",
        "get_absent_employees",
        "get_team_employee_list",
    ):
        if params.get("date"):
            args["date_str"] = params["date"]
        if params.get("reporting_type") is not None:
            args["reporting_type"] = params["reporting_type"]
    elif tool_name == "get_attendance_history":
        if params.get("month"):
            args["month"] = params["month"]
        if params.get("year"):
            args["year"] = params["year"]
        if params.get("employee_id"):
            args["employee_id"] = params["employee_id"]
        if params.get("employee_name"):
            args["employee_name"] = params["employee_name"]
    elif tool_name == "search_employee":
        if params.get("employee_name"):
            args["query"] = params["employee_name"]
        elif params.get("employee_id"):
            args["query"] = str(params["employee_id"])
    elif tool_name == "get_employee_attendance_details":
        if params.get("employee_id"):
            args["employee_id"] = params["employee_id"]
        if params.get("employee_name"):
            args["employee_name"] = params["employee_name"]
        if params.get("date"):
            args["date_str"] = params["date"]
    return args


async def direct_tool_execution_node(
    state: AttendanceAgentState,
    config: RunnableConfig,
) -> Dict[str, Any]:
    """
    Execute the intent-mapped tool(s) directly — bypasses LLM tool selection.
    Used for summary, present, absent, and my_attendance queries.
    """
    selected = state.get("selected_tools") or []
    params = state.get("parameters") or {}
    intent = state.get("intent", "")

    if intent not in DIRECT_TOOL_INTENTS or not selected:
        return {}

    tool_calls = []
    tool_messages = []
    tool_results: dict[str, str] = {}

    for i, tool_name in enumerate(selected):
        tool_fn = _TOOLS_BY_NAME.get(tool_name)
        if not tool_fn:
            logger.warning("Unknown tool for direct execution: %s", tool_name)
            continue
        args = _build_tool_args(tool_name, params)
        call_id = f"direct_{tool_name}_{i}"
        logger.info("Direct tool execution: %s(%s) for intent=%s", tool_name, args, intent)
        try:
            result = await tool_fn.ainvoke(args, config=config)
        except Exception as exc:
            logger.error("Direct tool %s failed: %s", tool_name, exc, exc_info=True)
            result = json.dumps({"error": str(exc)})

        tool_calls.append({"name": tool_name, "args": args, "id": call_id, "type": "tool_call"})
        tool_messages.append(ToolMessage(content=str(result), tool_call_id=call_id))
        tool_results[tool_name] = str(result)

    if not tool_calls:
        return {}

    return {
        "messages": [AIMessage(content="", tool_calls=tool_calls), *tool_messages],
        "tool_results": tool_results,
        "final_response": None,
    }


# ── Node: agent (the core LLM call used in the ReAct loop) ───────────────────

def agent_node(state: AttendanceAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Core agent node: calls the LLM (with tools bound).
    The graph loops back here after each ToolMessage until stop condition.
    """
    messages = list(state["messages"])

    # Remove any orphaned tool calls left over from interrupted/rapid turns
    # before the LLM sees the history (prevents OpenAI 400 Bad Request).
    messages = _sanitize_messages(messages)

    # Build system message with the real authenticated user's info from config
    cfg = config.get("configurable", {}) if config else {}
    full_name = cfg.get("full_name", "User")
    employee_id = cfg.get("employee_id", 0)

    if messages and not isinstance(messages[0], SystemMessage):
        sys_msg = build_system_message(full_name, employee_id)
        messages = [sys_msg] + messages

    # On the first agent turn, inject intent-based tool routing so the LLM
    # picks the correct tool (e.g. summary vs my_attendance).
    has_tool_results = any(isinstance(m, ToolMessage) for m in messages)
    if not has_tool_results:
        routing_hint = _build_tool_routing_hint(state)
        if routing_hint:
            messages = messages + [SystemMessage(content=routing_hint)]
        last_emp = _format_last_employee_context(state)
        if last_emp:
            messages = messages + [
                SystemMessage(content=f"Session context: {last_emp}. Use for follow-up references.")
            ]

    response = _llm_with_tools.invoke(messages)
    return {"messages": [response]}


def _persist_employee_context(
    state: AttendanceAgentState,
    turn_messages: list,
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """Merge last-discussed employee from params and tool output into the graph result."""
    params = state.get("parameters") or {}
    if params.get("employee_name"):
        result["last_employee_name"] = str(params["employee_name"]).strip()
    if params.get("employee_id"):
        try:
            result["last_employee_id"] = int(params["employee_id"])
        except (TypeError, ValueError):
            pass

    tool_emp_id, tool_emp_name = _extract_employee_from_tool_results(
        state.get("tool_results") or _tool_results_from_messages(turn_messages)
    )
    if tool_emp_id:
        result["last_employee_id"] = tool_emp_id
    if tool_emp_name:
        result["last_employee_name"] = tool_emp_name
    return result


def _tool_results_from_messages(turn_messages: list) -> dict[str, str]:
    """Build a tool_name → content map from ToolMessages in the current turn."""
    out: dict[str, str] = {}
    for msg in turn_messages:
        if isinstance(msg, ToolMessage) and msg.content:
            out[f"tool_{len(out)}"] = str(msg.content)
    return out


# ── Node: response generation ─────────────────────────────────────────────────

def response_generation_node(state: AttendanceAgentState) -> Dict[str, Any]:
    """
    Build the final user-facing response from THIS turn's tool results only.
    Ignores assistant messages and tool outputs from earlier turns.
    """
    messages = state["messages"]
    turn_messages = _current_turn_messages(messages)
    intent = state.get("intent", "")

    # Deterministic plain text for personal attendance (no table)
    if intent == "my_attendance":
        personal = try_format_my_attendance_from_turn(state.get("tool_results"), turn_messages)
        if personal:
            return _persist_employee_context(
                state, turn_messages, {"final_response": personal}
            )

    # Deterministic monthly history / month-to-date summary
    if intent == "history_query":
        summary_style = wants_monthly_summary_style(
            next((m.content for m in turn_messages if isinstance(m, HumanMessage)), "")
        )
        history_formatted = try_format_history_from_turn(
            state.get("tool_results"),
            turn_messages,
            summary_style=summary_style,
        )
        if history_formatted:
            return _persist_employee_context(
                state, turn_messages, {"final_response": history_formatted}
            )

    # Deterministic plain text for a specific employee's attendance on a date
    if intent == "employee_detail":
        detail_formatted = try_format_employee_detail_from_turn(
            state.get("tool_results"), turn_messages
        )
        if detail_formatted:
            return _persist_employee_context(
                state, turn_messages, {"final_response": detail_formatted}
            )

    # Deterministic employee list (ID + name) for present/absent/search
    if intent != "employee_detail":
        list_formatted = try_format_list_from_turn(state.get("tool_results"), turn_messages)
        if list_formatted:
            return _persist_employee_context(
                state, turn_messages, {"final_response": list_formatted}
            )

    # Agent-loop text reply from the current turn (not from prior turns)
    for msg in reversed(turn_messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            return _persist_employee_context(
                state, turn_messages, {"final_response": msg.content}
            )

    last_human = next(
        (m.content for m in turn_messages if isinstance(m, HumanMessage)), ""
    )

    # Prefer structured tool_results set by direct_tool_execution_node
    stored = state.get("tool_results") or {}
    if stored:
        tool_contents = list(stored.values())
    else:
        tool_contents = [
            m.content for m in turn_messages
            if isinstance(m, ToolMessage) and m.content
        ]

    if tool_contents:
        if intent == "my_attendance":
            style_hint = (
                "Reply in plain text only (2-4 short sentences). "
                "Do NOT use markdown tables.\n"
            )
        elif intent == "history_query":
            style_hint = (
                " Show a markdown table with columns Date | Status "
                "(mark each day Present, Absent, Leave, or Holiday). "
                "Include summary counts at the top.\n"
            )
        elif intent == "employee_detail":
            style_hint = (
                " Reply in plain text only (status, check-in, check-out, worked hours). "
                "Do NOT show a search results table.\n"
            )
        elif intent in ("present_query", "absent_query", "search_employee", "team_list_query"):
            style_hint = (
                " When listing employees, show ONLY Employee ID and Name in a markdown table.\n"
            )
        else:
            style_hint = (
                " Use clear plain text or bullet points. "
                "Do NOT use markdown tables unless listing multiple employees.\n"
            )
        fallback_prompt = (
            f'The user asked: "{last_human}"\n'
            f'Detected intent: {intent}\n\n'
            "Answer ONLY using the live HRMS data below from THIS request. "
            f"{style_hint}\n\n"
            f"Tool results:\n" + "\n\n".join(tool_contents)
        )
        summary = _llm.invoke([HumanMessage(content=fallback_prompt)])
        result: Dict[str, Any] = {"final_response": summary.content}
    else:
        result = {"final_response": "I was unable to retrieve the requested data. Please try again."}

    return _persist_employee_context(state, turn_messages, result)
