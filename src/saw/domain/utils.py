"""Shared utility functions for the SAW domain layer."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)
