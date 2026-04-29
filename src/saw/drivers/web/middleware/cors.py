"""CORS configuration for FastAPI.

Per D-03: CORS middleware allows localhost:3000 for frontend development.
"""
from typing import List

DEFAULT_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def get_cors_origins(origins: List[str] | None = None) -> List[str]:
    """Get CORS origins with defaults.

    Args:
        origins: Custom origins list. If None, returns defaults.

    Returns:
        List of allowed CORS origins.
    """
    return origins or DEFAULT_CORS_ORIGINS