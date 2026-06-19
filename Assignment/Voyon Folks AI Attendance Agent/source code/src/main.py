"""FastAPI application entry point for the Voyon Attendance Agent."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.routers.auth_router import router as auth_router, get_session
from src.routers.chat_router import router as chat_router
from src.config import settings

logging.basicConfig(
    level=logging.DEBUG if settings.app_debug else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Voyon Attendance Agent",
    description="AI-powered attendance assistant for Voyon Folks HRMS",
    version="1.0.0",
)

# ── Templates & static files ──────────────────────────────────────────────────

_src = Path(__file__).parent
_templates_dir = _src / "templates"
_static_dir = _src / "static"

templates = Jinja2Templates(directory=str(_templates_dir))
app.state.templates = templates

if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(chat_router)


# ── Root page ─────────────────────────────────────────────────────────────────

@app.get("/")
async def index(request: Request):
    session = get_session(request)
    if not session:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "full_name": session.full_name,
            "employee_id": session.employee_id,
        },
    )


# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "voyon-attendance-agent"}


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
