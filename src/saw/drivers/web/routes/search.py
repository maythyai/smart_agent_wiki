"""Search API route for BM25 + FTS5 search.

Per D-07: GET /api/search endpoint.
Per D-08: Results include snippet, citation, confidence, freshness.
Per D-09: Support pagination and filtering by type/tag/min_confidence.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Request

from saw.drivers.web.schemas.search import SearchResponse, SearchResult

if TYPE_CHECKING:
    from saw.engines.query.engine import QueryEngine

router = APIRouter()


def get_query_engine(request: Request) -> QueryEngine:
    """Dependency: get QueryEngine from app.state."""
    return request.app.state.query


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Results per page"),
    type: str | None = Query(None, description="Filter by page type"),
    tag: str | None = Query(None, description="Filter by tag"),
    min_confidence: int | None = Query(None, ge=1, le=4, description="Min confidence level"),
    engine: QueryEngine = Depends(get_query_engine),
) -> SearchResponse:
    """Search knowledge base using BM25 + FTS5 (per D-07).

    Per D-08: Results include snippet, citation, confidence.
    Per D-09: Support pagination and filtering.

    Args:
        q: Search query string (required, min 1 char).
        page: Page number for pagination (default 1).
        per_page: Results per page (default 10, max 100).
        type: Optional filter by page type.
        tag: Optional filter by tag.
        min_confidence: Optional minimum confidence level (1-4).
        engine: QueryEngine dependency.

    Returns:
        SearchResponse with paginated results.
    """
    # Execute search via QueryEngine. F-QS-01: fetch a generous window so
    # client-side type/tag/confidence filters and pagination operate over the
    # full match set instead of only the first 20 hits (which made page >=3
    # return empty). The engine threads limit/offset into FTS5.
    result = engine.query(question=q, mode="search", limit=500)

    # Convert QueryResult to SearchResponse
    results: list[SearchResult] = []
    for source in result.sources:
        # Apply confidence filter
        confidence_value = source.get("confidence", 1)
        if isinstance(confidence_value, str):
            # Map string to int
            conf_map = {
                "unverified": 1,
                "single_source": 2,
                "cross_validated": 3,
                "human_verified": 4,
            }
            confidence_int = conf_map.get(confidence_value.lower(), 1)
        else:
            confidence_int = int(confidence_value)

        if min_confidence is not None and confidence_int < min_confidence:
            continue

        # Apply type filter
        if type is not None and source.get("type") != type:
            continue

        # Apply tag filter (if source has tags)
        if tag is not None and tag not in source.get("tags", []):
            continue

        # Create snippet (truncate to 200 chars)
        content = source.get("content", "")
        snippet = content[:200] + "..." if len(content) > 200 else content

        results.append(
            SearchResult(
                slug=source.get("slug", source.get("claim_uuid", "")),
                title=source.get("title", source.get("claim_uuid", "")),
                snippet=snippet,
                confidence=confidence_int,
                freshness=source.get("freshness", 0),
                citations=[f"claim:{source.get('claim_uuid', '')}"],
                score=source.get("score", 0.0),
            )
        )

    # Pagination
    total = len(results)
    offset = (page - 1) * per_page
    paginated = results[offset : offset + per_page]

    return SearchResponse(
        results=paginated,
        total=total,
        page=page,
        per_page=per_page,
        has_more=offset + per_page < total,
    )


@router.get("/search/suggestions")
async def search_suggestions(
    q: str = Query(..., min_length=1, description="Partial query"),
    limit: int = Query(5, ge=1, le=20, description="Max suggestions"),
    engine: QueryEngine = Depends(get_query_engine),
) -> list[str]:
    """Get search suggestions based on partial query.

    Args:
        q: Partial query string.
        limit: Maximum number of suggestions (default 5, max 20).
        engine: QueryEngine dependency.

    Returns:
        List of suggested search titles.
    """
    # Use FTS5 prefix search via QueryEngine
    result = engine.query(question=q, mode="search")

    # Extract unique titles
    titles: list[str] = []
    seen: set[str] = set()
    for source in result.sources[: limit * 2]:
        title = source.get("title", "")
        if title and title not in seen:
            titles.append(title)
            seen.add(title)
        if len(titles) >= limit:
            break

    return titles
