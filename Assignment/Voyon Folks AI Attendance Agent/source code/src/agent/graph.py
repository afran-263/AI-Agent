"""Build and compile the LangGraph Attendance Agent workflow.

Workflow graph:
    START
      │
      ▼
  intent_detection → parameter_extraction → context_enrichment → tool_selection
      │
      ├── (DIRECT_TOOL_INTENTS) ──► direct_tools ──► response_generation ──► END
      │
      └── agent ◄──► tools  [ReAct loop]
              │
              └── response_generation ──► END
"""
from __future__ import annotations

import logging
from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.agent.state import AttendanceAgentState
from src.agent.nodes import (
    agent_node,
    tool_executor,
    intent_detection_node,
    parameter_extraction_node,
    context_enrichment_node,
    tool_selection_node,
    direct_tool_execution_node,
    response_generation_node,
    DIRECT_TOOL_INTENTS,
    _current_turn_messages,
)

logger = logging.getLogger(__name__)

# ── Routing functions ─────────────────────────────────────────────────────────

def route_after_agent(state: AttendanceAgentState) -> Literal["tools", "response_generation"]:
    """Route: does the LLM want to call tools, or is it done?"""
    messages = state["messages"]
    last_msg = messages[-1] if messages else None

    if isinstance(last_msg, AIMessage) and last_msg.tool_calls:
        return "tools"
    return "response_generation"


def route_after_tool_selection(
    state: AttendanceAgentState,
) -> Literal["direct_tools", "agent"]:
    """Route: direct tool call or LLM agent loop."""
    intent = state.get("intent", "")
    if intent in DIRECT_TOOL_INTENTS and state.get("selected_tools"):
        return "direct_tools"
    return "agent"


# ── Graph construction ────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Build but do not compile the StateGraph."""
    graph = StateGraph(AttendanceAgentState)

    graph.add_node("intent_detection", intent_detection_node)
    graph.add_node("parameter_extraction", parameter_extraction_node)
    graph.add_node("context_enrichment", context_enrichment_node)
    graph.add_node("tool_selection", tool_selection_node)
    graph.add_node("direct_tools", direct_tool_execution_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_executor)
    graph.add_node("response_generation", response_generation_node)

    graph.add_edge(START, "intent_detection")
    graph.add_edge("intent_detection", "parameter_extraction")
    graph.add_edge("parameter_extraction", "context_enrichment")
    graph.add_edge("context_enrichment", "tool_selection")

    graph.add_conditional_edges(
        "tool_selection",
        route_after_tool_selection,
        {
            "direct_tools": "direct_tools",
            "agent": "agent",
        },
    )

    graph.add_edge("direct_tools", "response_generation")

    graph.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            "response_generation": "response_generation",
        },
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("response_generation", END)

    return graph


# ── Compiled graph (singleton) ────────────────────────────────────────────────

_checkpointer = MemorySaver()

compiled_graph = build_graph().compile(checkpointer=_checkpointer)

logger.info("Attendance Agent graph compiled successfully.")


# ── Public helper ─────────────────────────────────────────────────────────────

async def run_agent(
    user_message: str,
    session_id: str,
    jwt_token: str,
    employee_id: int,
    full_name: str,
) -> dict:
    """
    Invoke the agent graph for a given conversation thread.

    Returns a dict: {"response": str}
    """
    from langchain_core.messages import HumanMessage

    thread_config = {
        "configurable": {
            "thread_id": session_id,
            "jwt_token": jwt_token,
            "employee_id": employee_id,
            "full_name": full_name,
        }
    }

    input_messages = {
        "messages": [HumanMessage(content=user_message)],
        "final_response": None,
        "tool_results": None,
    }

    try:
        result = await compiled_graph.ainvoke(input_messages, config=thread_config)
    except Exception as exc:
        logger.error("Agent graph error: %s", exc, exc_info=True)
        return {
            "response": "I encountered an error while processing your request. Please try again.",
        }

    response = result.get("final_response") or ""
    if not response:
        turn_messages = _current_turn_messages(result.get("messages", []))
        for msg in reversed(turn_messages):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                response = msg.content
                break

    return {
        "response": response or "I was unable to generate a response. Please try again.",
    }
