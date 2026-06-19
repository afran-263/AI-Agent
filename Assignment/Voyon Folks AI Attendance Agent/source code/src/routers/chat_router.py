"""Chat API endpoints — drives the LangGraph attendance agent."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from src.models.schemas import ChatRequest, ChatResponse
from src.routers.auth_router import get_session
from src.agent.graph import run_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


def _require_session(request: Request):
    session = get_session(request)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")
    return session


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    """
    Send a message to the Attendance Agent.

    The agent:
    1. Detects intent
    2. Extracts parameters
    3. Selects and executes tools against live HRMS APIs
    4. Returns a natural-language response
    """
    session = _require_session(request)

    user_message = body.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    result = await run_agent(
        user_message=user_message,
        session_id=session.session_id,
        jwt_token=session.jwt_token,
        employee_id=session.employee_id,
        full_name=session.full_name,
    )

    return ChatResponse(reply=result["response"])


@router.get("/me")
async def me(request: Request):
    """Return the currently authenticated user's identity."""
    session = _require_session(request)
    return JSONResponse({
        "full_name": session.full_name,
        "employee_id": session.employee_id,
        "user_id": session.user_id,
    })
