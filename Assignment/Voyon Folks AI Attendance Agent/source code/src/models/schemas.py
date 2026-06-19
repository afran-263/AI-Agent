"""Pydantic models for request/response schemas."""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


# ── Authentication ────────────────────────────────────────────────────────────

class UserSession(BaseModel):
    """Stored in the server-side session dict keyed by session_id."""
    session_id: str
    jwt_token: str
    refresh_token: str
    employee_id: int
    user_id: int
    full_name: str
    thread_id: str  # LangGraph conversation thread (= session_id)


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str           # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    error: Optional[str] = None
