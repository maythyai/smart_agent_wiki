"""Timeline API endpoints.

Provides chronological view of wiki pages grouped by date.
"""
from __future__ import annotations

import os
from datetime import datetime, date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from saw.drivers.web.schemas.timeline import (
    TimelineEntry,
    TimelineDay,
    TimelineResponse,
    DailyNoteRequest,
    DailyNoteResponse,
)

router = APIRouter(prefix="/api/timeline", tags=["timeline"])


def get_wiki_repo(request: Request):
    """Get WikiRepository from app state."""
    if hasattr(request.app.state, "wiki_repo"):
        return request.app.state.wiki_repo
    raise HTTPException(status_code=500, detail="Wiki repository not initialized")


def get_write_queue(request: Request):
    """Get WriteQueue from app state."""
    if hasattr(request.app.state, "write_queue"):
        return request.app.state.write_queue
    raise HTTPException(status_code=500, detail="Write queue not initialized")


@router.get("", response_model=TimelineResponse)
async def get_timeline(
    start_date: str | None = None,
    end_date: str | None = None,
    entity_type: str | None = None,
    tag: str | None = None,
    limit: int = 30,
    wiki_repo=Depends(get_wiki_repo),
) -> TimelineResponse:
    """Get timeline of pages grouped by date.

    Args:
        start_date: Filter pages after this date (ISO format)
        end_date: Filter pages before this date (ISO format)
        entity_type: Filter by entity type
        tag: Filter by tag
        limit: Max number of days to return (default 30)

    Returns:
        TimelineResponse with days grouped chronologically
    """
    # Parse date filters
    filter_start = None
    filter_end = None
    if start_date:
        try:
            filter_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    if end_date:
        try:
            filter_end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")

    # Collect all pages with dates
    pages_with_dates: list[tuple[date, str, Any]] = []

    for slug in wiki_repo.list_pages():
        page_path = wiki_repo._root / slug
        page = wiki_repo.read(slug)
        if not page:
            continue

        # Apply filters
        if entity_type and page.entity_type != entity_type:
            continue
        if tag and tag not in page.tags:
            continue

        # Get date from frontmatter or file mtime
        page_date = None
        if hasattr(page, "frontmatter") and page.frontmatter:
            fm_date = page.frontmatter.get("created_at") or page.frontmatter.get("date")
            if fm_date:
                try:
                    if isinstance(fm_date, str):
                        page_date = datetime.fromisoformat(fm_date.replace("Z", "+00:00")).date()
                    elif hasattr(fm_date, "year"):
                        page_date = fm_date
                except (ValueError, AttributeError):
                    pass

        # Fallback to file modification time
        if page_date is None and page_path.exists():
            mtime = os.path.getmtime(page_path)
            page_date = datetime.fromtimestamp(mtime).date()

        if page_date is None:
            continue

        # Apply date filters
        if filter_start and page_date < filter_start:
            continue
        if filter_end and page_date > filter_end:
            continue

        pages_with_dates.append((page_date, slug, page))

    # Sort by date descending (newest first)
    pages_with_dates.sort(key=lambda x: x[0], reverse=True)

    # Group by day
    days_map: dict[str, list[TimelineEntry]] = {}
    for page_date, slug, page in pages_with_dates:
        date_str = page_date.isoformat()
        if date_str not in days_map:
            days_map[date_str] = []

        # Check if this is a daily note
        is_daily_note = "daily-note" in slug.lower() or page.entity_type == "daily_note"

        entry = TimelineEntry(
            slug=slug,
            title=page.title,
            entity_type=page.entity_type,
            date=date_str,
            time=None,  # Could extract from created_at if available
            snippet=page.content[:150] if page.content else "",
            is_daily_note=is_daily_note,
            tags=page.tags,
        )
        days_map[date_str].append(entry)

    # Build TimelineDay objects
    days: list[TimelineDay] = []
    for date_str in sorted(days_map.keys(), reverse=True)[:limit]:
        entries = days_map[date_str]
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = dt.strftime("%A")

        # Find daily note slug if exists
        daily_note_slug = None
        for entry in entries:
            if entry.is_daily_note:
                daily_note_slug = entry.slug
                break

        days.append(
            TimelineDay(
                date=date_str,
                day_name=day_name,
                entries=entries,
                daily_note_slug=daily_note_slug,
            )
        )

    # Calculate date range
    if pages_with_dates:
        date_range = {
            "start": min(p[0] for p in pages_with_dates).isoformat(),
            "end": max(p[0] for p in pages_with_dates).isoformat(),
        }
    else:
        today = date.today().isoformat()
        date_range = {"start": today, "end": today}

    total_entries = sum(len(entries) for entries in days_map.values())
    has_more = len(days_map) > limit

    return TimelineResponse(
        days=days,
        total_entries=total_entries,
        date_range=date_range,
        has_more=has_more,
    )


@router.post("/daily-note", response_model=DailyNoteResponse)
async def create_daily_note(
    request: DailyNoteRequest,
    wiki_repo=Depends(get_wiki_repo),
    write_queue=Depends(get_write_queue),
) -> DailyNoteResponse:
    """Create or retrieve a daily note for the specified date.

    Args:
        request: Date for the daily note (defaults to today)

    Returns:
        DailyNoteResponse with slug and status
    """
    # Parse date
    if request.date:
        try:
            note_date = datetime.strptime(request.date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    else:
        note_date = date.today()

    # Generate slug
    slug = f"daily-note-{note_date.isoformat()}"

    # Check if already exists
    existing = wiki_repo.read(slug)
    if existing:
        return DailyNoteResponse(
            slug=slug,
            status="exists",
            exists=True,
        )

    # Create new daily note
    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp

    title = f"Daily Note — {note_date.strftime('%B %d, %Y')}"
    content = f"""# {title}

**Date:** {note_date.isoformat()}
**Day:** {note_date.strftime('%A')}

## Today's Focus
- [ ]

## Notes


## Tasks
- [ ]

## Reflections


---
*Created automatically via Timeline*
"""

    write_op = WriteOp(
        op_type="create_page",
        payload={
            "slug": slug,
            "title": title,
            "content": content,
            "entity_type": "note",
            "properties": {"date": note_date.isoformat()},
            "tags": ["daily-note"],
        },
        status=WriteOpStatus.PENDING,
    )

    write_queue.enqueue(write_op)

    return DailyNoteResponse(
        slug=slug,
        status="created",
        exists=False,
    )
