"""LangGraph state definition for the Attendance Agent."""
from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AttendanceAgentState(TypedDict):
    """
    The complete state object carried through the LangGraph workflow.

    Workflow:
        user_query ──► intent_detection ──► parameter_extraction
                    ──► context_enrichment ──► tool_selection
                    ──► direct_tools | agent ReAct loop
                    ──► response_generation
    """

    # ── Conversation messages (auto-appended by add_messages reducer) ─────────
    messages: Annotated[List[BaseMessage], add_messages]

    # ── Detected intent ───────────────────────────────────────────────────────
    # Possible values:
    #   present_query | absent_query | summary_query | team_list_query |
    #   history_query | employee_detail | search_employee | my_attendance |
    #   unclear | out_of_scope
    intent: Optional[str]

    # ── Extracted parameters (dates, employee names/IDs, month, year…) ────────
    parameters: Optional[Dict[str, Any]]

    # ── Which tools the tool_selection node decided to invoke ─────────────────
    selected_tools: Optional[List[str]]

    # ── Raw results from API calls ────────────────────────────────────────────
    tool_results: Optional[Dict[str, Any]]

    # ── Conversation memory (persisted across turns in the same session) ───────
    last_employee_id: Optional[int]
    last_employee_name: Optional[str]

    # ── Final natural-language response ──────────────────────────────────────
    final_response: Optional[str]

    # ── Error message (if any API / processing step failed) ──────────────────
    error: Optional[str]
