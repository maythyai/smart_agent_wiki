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
    entity_type: str = "note"
    properties: dict[str, Any] = {}


class PageUpdate(BaseModel):
    """Page update request (per D-15)."""

    content: str
    message: str | None = None  # Commit message
    entity_type: str | None = None
    properties: dict[str, Any] | None = None


class PagePropertiesUpdate(BaseModel):
    """Partial update of a page's entity_type and/or properties."""

    entity_type: str | None = None
    properties: dict[str, Any] | None = None


class PageDelete(BaseModel):
    """Page delete request (per D-16)."""

    message: str | None = None  # Deletion reason


class PageListResponse(BaseModel):
    """List of wiki pages."""

    pages: list[PageResponse] = []
    slugs: list[str] = []
    total: int


class PageCreate(BaseModel):
    """Page creation request."""

    slug: str = Field(..., min_length=1, pattern=r"^[a-zA-Z0-9_-]+$")
    title: str = Field(..., min_length=1)
    content: str
    tags: list[str] = []
    type: str = "summary"
    entity_type: str = "note"
    properties: dict[str, Any] = {}


class PageStatus(BaseModel):
    """Write queue status response."""

    status: str
    slug: str
    op_id: str | None = None
    # F-WEB-10: optional warnings (e.g. backlink count) for destructive ops.
    warnings: list[str] | None = None


class QuickCaptureRequest(BaseModel):
    """Minimal page creation — title only, slug auto-generated."""

    title: str = Field(..., min_length=1, max_length=200)
    content: str = ""
    tags: list[str] = []


class QuickCaptureResponse(BaseModel):
    """Response after quick capture."""

    slug: str
    title: str
    status: str  # "queued"
