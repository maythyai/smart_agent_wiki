"""Search API schemas for request/response validation.

Per D-07: GET /api/search endpoint with BM25 + FTS5 search.
Per D-08: Results include snippet, citation, confidence.
Per D-09: Support pagination and filtering.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Search query parameters (per D-07~09)."""

    q: str = Field(..., min_length=1, description="Search query")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(10, ge=1, le=100, description="Results per page")
    type: str | None = Field(None, description="Filter by page type")
    tag: str | None = Field(None, description="Filter by tag")
    min_confidence: int | None = Field(None, ge=1, le=4, description="Min confidence level")


class SearchResult(BaseModel):
    """Single search result (per D-08)."""

    slug: str
    title: str
    snippet: str
    confidence: int = Field(..., ge=1, le=4)
    freshness: int = Field(..., ge=0, le=8)
    citations: list[str]
    score: float = Field(..., ge=0.0)


class SearchResponse(BaseModel):
    """Paginated search results."""

    results: list[SearchResult]
    total: int
    page: int
    per_page: int
    has_more: bool
