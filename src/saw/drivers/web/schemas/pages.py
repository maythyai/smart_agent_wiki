"""Page API schemas for request/response validation.

Per D-13: GET /api/pages - list all wiki pages.
Per D-14: GET /api/pages/{slug} - get page content.
Per D-15: PUT /api/pages/{slug} - update page via Write Queue.
Per D-16: DELETE /api/pages/{slug} - delete page via Write Queue.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PageResponse(BaseModel):
    """Wiki page content (per D-14)."""

    slug: str
    title: str
    content: str
    frontmatter: dict[str, Any]
    confidence: int = Field(..., ge=1, le=4)
    freshness: int = Field(..., ge=0, le=8)


class PageUpdate(BaseModel):
    """Page update request (per D-15)."""

    content: str
    message: str | None = None  # Commit message


class PageDelete(BaseModel):
    """Page delete request (per D-16)."""

    message: str | None = None  # Deletion reason


class PageListResponse(BaseModel):
    """List of wiki pages."""

    slugs: list[str]
    total: int


class PageCreate(BaseModel):
    """Page creation request."""

    slug: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    title: str = Field(..., min_length=1)
    content: str
    tags: list[str] = []
    type: str = "summary"


class PageStatus(BaseModel):
    """Write queue status response."""

    status: str
    slug: str
    op_id: str | None = None
