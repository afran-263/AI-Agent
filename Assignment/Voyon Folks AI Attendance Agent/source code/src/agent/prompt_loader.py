"""Load the agent system prompt from an external file."""
from __future__ import annotations

import logging
from pathlib import Path

from src.config import settings

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_FALLBACK_PROMPT = (
    "You are the Voyon Attendance Agent. Answer attendance questions using tools only. "
    "Current user: {full_name} (Employee ID: {employee_id}). Today's date: {today}."
)


def load_system_prompt_template() -> str:
    """
    Load the system prompt template from SYSTEM_PROMPT_FILE (relative to project root).

    The file may contain placeholders: {full_name}, {employee_id}, {today}
  """
    prompt_file = settings.system_prompt_file
    if not prompt_file:
        logger.warning("SYSTEM_PROMPT_FILE is not set. Using fallback prompt.")
        return _FALLBACK_PROMPT

    full_path = Path(prompt_file) if Path(prompt_file).is_absolute() else _PROJECT_ROOT / prompt_file

    if not full_path.exists():
        logger.warning("System prompt file not found at %s. Using fallback.", full_path)
        return _FALLBACK_PROMPT

    content = full_path.read_text(encoding="utf-8").strip()
    if not content:
        logger.warning("System prompt file %s is empty. Using fallback.", full_path)
        return _FALLBACK_PROMPT

    logger.info("Loaded system prompt from %s (%d chars).", full_path, len(content))
    return content
