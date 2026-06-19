"""Authentication routes: login, logout, token refresh."""
from __future__ import annotations

import secrets
import logging
from typing import Annotated

from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from src.api.hrms_client import HrmsClient, HrmsApiError
from src.models.schemas import UserSession
from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Session store (in-memory, production should use Redis) ───────────────────
# Maps session_id → UserSession
_sessions: dict[str, UserSession] = {}


def get_session(request: Request) -> UserSession | None:
    """Retrieve the active UserSession from the signed cookie, or None."""
    from itsdangerous import URLSafeSerializer, BadSignature
    ser = URLSafeSerializer(settings.app_secret_key, salt="session")
    session_id: str | None = request.cookies.get("attend_session")
    if not session_id:
        return None
    try:
        validated_id: str = ser.loads(session_id)
    except BadSignature:
        return None
    return _sessions.get(validated_id)


def _sign_session_id(session_id: str) -> str:
    from itsdangerous import URLSafeSerializer
    ser = URLSafeSerializer(settings.app_secret_key, salt="session")
    return ser.dumps(session_id)


@router.get("/login")
async def login_page(request: Request):
    templates: Jinja2Templates = request.app.state.templates
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    try:
        data = await HrmsClient.login(username, password)
    except HrmsApiError as exc:
        _templates: Jinja2Templates = request.app.state.templates
        return _templates.TemplateResponse(
            request,
            "login.html",
            {"error": str(exc)},
            status_code=400,
        )

    # Build session
    session_id = secrets.token_urlsafe(32)
    session = UserSession(
        session_id=session_id,
        jwt_token=data.get("token", ""),
        refresh_token=data.get("refreshToken", ""),
        employee_id=int(data.get("employeeId", 0)),
        user_id=int(data.get("userId", 0)),
        full_name=data.get("userName", data.get("fullName", username)),
        thread_id=session_id,
    )
    _sessions[session_id] = session

    signed = _sign_session_id(session_id)
    redirect = RedirectResponse(url="/", status_code=302)
    redirect.set_cookie(
        "attend_session",
        signed,
        httponly=True,
        samesite="lax",
        secure=False,   # set True when served over HTTPS
        max_age=60 * 60 * 8,
    )
    return redirect


@router.post("/logout")
async def logout(request: Request):
    session = get_session(request)
    if session:
        _sessions.pop(session.session_id, None)

    redirect = RedirectResponse(url="/login", status_code=302)
    redirect.delete_cookie("attend_session")
    return redirect
