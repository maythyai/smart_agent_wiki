"""Default configuration values and templates."""
from __future__ import annotations

from typing import Any

# Default wiki configuration
DEFAULT_CONFIG: dict[str, Any] = {
    "path": ".",
    "agent": None,
    "llm": {
        "extraction_model": "",
        "query_model": "",
        "api_key": "",
    },
}

# WIP file template (per D-23)
WIP_TEMPLATE: dict[str, Any] = {
    "active_tasks": [],
    "next_steps": [],
    "pending_questions": [],
    "last_session": "",
}
