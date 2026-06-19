"""Application configuration loaded from environment variables / .env file."""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (one level above src/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)


class Settings:
    # ── HRMS ──────────────────────────────────────────────────────────────────
    hrms_base_url: str = os.getenv("HRMS_BASE_URL", "https://localhost:44360")
    hrms_login_path: str = os.getenv("HRMS_LOGIN_PATH", "/m/api/Login/LoginUser")
    hrms_ssl_verify: bool = os.getenv("HRMS_SSL_VERIFY", "false").lower() == "true"

    # ── Azure OpenAI ──────────────────────────────────────────────────────────
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")

    # ── Application ───────────────────────────────────────────────────────────
    app_secret_key: str = os.getenv("APP_SECRET_KEY", "dev-secret-change-in-production")
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8080"))
    app_debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    system_prompt_file: str = os.getenv("SYSTEM_PROMPT_FILE", "systemprompt.txt")


settings = Settings()
