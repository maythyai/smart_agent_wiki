"""Timeline schemas for chronological page view.

Provides schemas for timeline entries grouped by date.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class TimelineEntry(BaseModel):
    """Single timeline entry."""

    slug: str
    title: str
    entity_type: str = "note"
    date: str  # ISO date "2024-05-15"
    time: str | None = None  # ISO time "14:30:00"
    snippet: str  # First 150 chars
    is_daily_note: bool = False
    tags: list[str] = []


class TimelineDay(BaseModel):
    """Group of entries for a single day."""

    date: str  # ISO date "2024-05-15"
    day_name: str  # "Wednesday"
    entries: list[TimelineEntry]
    daily_note_slug: str | None = None


class TimelineResponse(BaseModel):
    """Timeline response with days and metadata."""

    days: list[TimelineDay]
    total_entries: int
    date_range: dict  # { start: "2024-01-01", end: "2024-05-15" }
    has_more: bool


class DailyNoteRequest(BaseModel):
    """Request to create/get daily note."""

    date: str | None = None  # ISO date, defaults to today


class DailyNoteResponse(BaseModel):
    """Response for daily note creation."""

    slug: str
    status: str  # "created" or "exists"
    exists: bool
