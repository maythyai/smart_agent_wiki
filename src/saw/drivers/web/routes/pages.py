"""Page API endpoints.

Per D-13: GET /api/pages - list all wiki pages.
Per D-14: GET /api/pages/{slug} - get page content.
Per D-15: PUT /api/pages/{slug} - update page via Write Queue.
Per D-16: DELETE /api/pages/{slug} - delete page via Write Queue.

Bidirectional linking:
- GET /api/pages/{slug}/backlinks - pages linking TO this page
- GET /api/pages/{slug}/outlinks - pages this page links TO

All mutations flow through Write Queue for durability (per ARCHITECTURE.md).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request

from saw.drivers.web.schemas.pages import (
    PageCreate,
    PageDelete,
    PageListResponse,
    PagePropertiesUpdate,
    PageResponse,
    PageStatus,
    PageUpdate,
)
from saw.engines.query.wiki_links import extract_unique_targets, parse_wiki_links

router = APIRouter()


def get_query_engine(request: Request):
    """Dependency: get QueryEngine from app.state."""
    return request.app.state.query


def get_write_queue(request: Request):
    """Dependency: get WriteQueue from app.state."""
    return request.app.state.write_queue


@router.get("/pages", response_model=PageListResponse)
async def list_pages(
    q: str | None = None,
    entity_type: str | None = None,
    limit: int = Query(50, ge=1, le=200, description="Page size (hard-capped at 200)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    engine=Depends(get_query_engine),
) -> PageListResponse:
    """List all wiki pages with optional search (per D-13).

    Returns full page objects for listing and search results.
    """
    slug_list: list[str] = []
    wiki = getattr(engine, "_wiki_repo", None) or getattr(engine, "wiki", None)
    if wiki is not None:
        slug_list = wiki.list_pages()

    # F-WEB-01: filter BEFORE paginating. The previous code sliced the slug
    # list into a window first and then applied q/entity_type filters inside
    # that window — so any match outside the current window was invisible and
    # a filtered search could return empty results. We now stream all slugs,
    # apply filters, and materialise PageResponse objects only for the
    # requested [offset, offset+limit) window (memory stays bounded by the
    # page size, not the whole wiki).
    pages: list[PageResponse] = []
    window_slugs: list[str] = []
    matched_total = 0
    end = offset + limit
    for slug in slug_list:
        page = wiki.read(slug) if wiki is not None else None
        if page is None:
            continue

        # Apply search filter
        if q:
            query_lower = q.lower()
            if (
                query_lower not in page.title.lower()
                and query_lower not in page.content.lower()
            ):
                continue

        # Apply entity_type filter
        if entity_type and page.entity_type != entity_type:
            continue

        # This slug matches the filters — only materialise the window.
        if offset <= matched_total < end:
            confidence_value = page.confidence.value if hasattr(page.confidence, "value") else 1
            freshness_value = page.freshness.value if hasattr(page.freshness, "value") else 0
            pages.append(
                PageResponse(
                    slug=slug,
                    title=page.title,
                    content=page.content,
                    frontmatter=page.frontmatter,
                    confidence=confidence_value,
                    freshness=freshness_value,
                    entity_type=page.entity_type,
                    properties=page.properties,
                )
            )
            window_slugs.append(slug)
        matched_total += 1

    return PageListResponse(
        pages=pages,
        slugs=window_slugs,
        total=matched_total,
    )


@router.get("/pages/{slug}", response_model=PageResponse)
async def get_page(
    slug: str = Path(..., description="Page slug"),
    engine=Depends(get_query_engine),
) -> PageResponse:
    """Get page content (per D-14).

    Returns the full content and metadata for a wiki page.
    Returns 404 if the page does not exist.
    """
    page = None
    if hasattr(engine, "_wiki_repo") and engine._wiki_repo is not None:
        page = engine._wiki_repo.read(slug)
    elif hasattr(engine, "wiki") and engine.wiki is not None:
        page = engine.wiki.read(slug)

    if page is None:
        raise HTTPException(status_code=404, detail=f"Page '{slug}' not found")

    # Map confidence and freshness from enum to int
    confidence_value = page.confidence.value if hasattr(page.confidence, "value") else 1
    freshness_value = page.freshness.value if hasattr(page.freshness, "value") else 0

    return PageResponse(
        slug=slug,
        title=page.title,
        content=page.content,
        frontmatter=page.frontmatter,
        confidence=confidence_value,
        freshness=freshness_value,
        entity_type=page.entity_type,
        properties=page.properties,
    )


@router.put("/pages/{slug}", response_model=PageStatus)
async def update_page(
    slug: str = Path(..., description="Page slug"),
    update: PageUpdate = ...,
    write_queue=Depends(get_write_queue),
) -> PageStatus:
    """Update page via Write Queue (per D-15).

    All mutations flow through Write Queue for durability.
    The update will be applied asynchronously by the Write Queue dispatcher.
    """
    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp

    op_id = str(uuid.uuid4())

    # Create write operations for wiki and index updates
    ops = [
        WriteOp(
            op_id=op_id,
            session_id="web-api",
            sink_name="wiki",
            payload={
                "op": "write",
                "slug": slug,
                "content": update.content,
                "message": update.message,
            },
            status=WriteOpStatus.PENDING,
        ),
        WriteOp(
            op_id=f"{op_id}-index",
            session_id="web-api",
            sink_name="fts5",
            payload={
                "op": "upsert",
                "slug": slug,
                "content": update.content,
            },
            status=WriteOpStatus.PENDING,
        ),
    ]

    # Enqueue atomically
    write_queue.enqueue_atomic(ops)

    return PageStatus(
        status="queued",
        slug=slug,
        op_id=op_id,
    )


@router.patch("/pages/{slug}/properties", response_model=PageStatus)
async def update_page_properties(
    slug: str = Path(..., description="Page slug"),
    update: PagePropertiesUpdate = ...,
    engine=Depends(get_query_engine),
    write_queue=Depends(get_write_queue),
) -> PageStatus:
    """Update a page's entity_type and/or properties via the Write Queue.

    Preserves the existing page content and all other frontmatter fields —
    only ``entity_type`` and ``properties`` are touched. Properties are merged
    into (not replacing) the existing property dict unless the caller supplies
    a full dict, in which case it overwrites.
    """
    wiki = getattr(engine, "_wiki_repo", None) or getattr(engine, "wiki", None)
    if wiki is None:
        raise HTTPException(status_code=503, detail="Wiki repository unavailable")

    existing = wiki.read(slug)
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Page '{slug}' not found")

    new_entity_type = update.entity_type or existing.entity_type
    if update.properties is not None:
        # Merge supplied properties over the existing ones.
        new_properties = {**existing.properties, **update.properties}
    else:
        new_properties = existing.properties

    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp

    op_id = str(uuid.uuid4())
    op = WriteOp(
        op_id=op_id,
        session_id="web-api",
        sink_name="wiki",
        payload={
            "op": "write",
            "slug": slug,
            "content": existing.content,
            "entity_type": new_entity_type,
            "properties": new_properties,
        },
        status=WriteOpStatus.PENDING,
    )
    write_queue.enqueue_atomic([op])

    return PageStatus(
        status="queued",
        slug=slug,
        op_id=op_id,
    )


@router.delete("/pages/{slug}", response_model=PageStatus)
async def delete_page(
    slug: str = Path(..., description="Page slug"),
    delete: PageDelete = None,
    write_queue=Depends(get_write_queue),
) -> PageStatus:
    """Delete page via Write Queue (per D-16).

    All mutations flow through Write Queue for durability.
    The deletion will be applied asynchronously by the Write Queue dispatcher.
    """
    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp

    op_id = str(uuid.uuid4())

    # Create delete operations for wiki and index
    ops = [
        WriteOp(
            op_id=op_id,
            session_id="web-api",
            sink_name="wiki",
            payload={
                "op": "delete",
                "slug": slug,
                "message": delete.message if delete else None,
            },
            status=WriteOpStatus.PENDING,
        ),
        WriteOp(
            op_id=f"{op_id}-index",
            session_id="web-api",
            sink_name="fts5",
            payload={
                "op": "delete",
                "slug": slug,
            },
            status=WriteOpStatus.PENDING,
        ),
    ]

    # Enqueue atomically
    write_queue.enqueue_atomic(ops)

    return PageStatus(
        status="queued",
        slug=slug,
        op_id=op_id,
    )


@router.get("/pages/{slug}/backlinks")
async def get_backlinks(
    slug: str = Path(..., description="Page slug"),
    engine=Depends(get_query_engine),
) -> list[dict]:
    """Get pages that link TO this page (backlinks).

    Scans all wiki pages to find which ones contain [[slug]] links.
    Returns list of {slug, title, context_snippet}.
    """
    wiki = getattr(engine, "_wiki_repo", None) or getattr(engine, "wiki", None)
    if wiki is None:
        return []

    backlinks: list[dict] = []
    target_slug = slug.strip("/")  # Normalize

    for page_slug in wiki.list_pages():
        if page_slug == slug:
            continue  # Skip self

        page = wiki.read(page_slug)
        if page is None:
            continue

        # Check if this page links to target
        links = parse_wiki_links(page.content)
        matching_links = [l for l in links if l.target == target_slug]

        if matching_links:
            # Extract context snippet around the link
            context = _extract_context(page.content, target_slug)
            backlinks.append({
                "slug": page_slug,
                "title": page.title,
                "context": context,
                "link_count": len(matching_links),
            })

    return backlinks


@router.get("/pages/{slug}/outlinks")
async def get_outlinks(
    slug: str = Path(..., description="Page slug"),
    engine=Depends(get_query_engine),
) -> list[dict]:
    """Get pages this page links TO (outlinks).

    Parses [[wiki-links]] from page content.
    Returns list of {target, alias, exists}.
    """
    wiki = getattr(engine, "_wiki_repo", None) or getattr(engine, "wiki", None)
    if wiki is None:
        return []

    page = wiki.read(slug)
    if page is None:
        raise HTTPException(status_code=404, detail=f"Page '{slug}' not found")

    links = parse_wiki_links(page.content)
    outlinks: list[dict] = []

    for link in links:
        # Check if target page exists
        target_page = wiki.read(link.target)
        outlinks.append({
            "target": link.target,
            "alias": link.alias,
            "section": link.section,
            "exists": target_page is not None,
        })

    return outlinks


@router.get("/pages/{slug}/related")
async def get_related_pages(
    slug: str = Path(..., description="Page slug"),
    top_k: int = 8,
    engine=Depends(get_query_engine),
) -> list[dict]:
    """Get pages related to this page.

    Uses 3-signal scoring: shared tags, shared links, type affinity.
    Returns list of {slug, title, score, reasons}.
    """
    from saw.engines.query.related_pages import compute_related_pages

    wiki = getattr(engine, "_wiki_repo", None) or getattr(engine, "wiki", None)
    if wiki is None:
        return []

    return compute_related_pages(slug, wiki, top_k=top_k)


def _extract_context(content: str, target_slug: str, context_chars: int = 80) -> str:
    """Extract text snippet around a [[wiki-link]] reference.

    Args:
        content: Page content.
        target_slug: The slug being linked to.
        context_chars: Characters of context on each side.

    Returns:
        Snippet with ... ellipsis for truncated text.
    """
    import re
    # Find [[target]] or [[target|alias]] in content
    pattern = rf'\[\[{re.escape(target_slug)}[^]]*\]\]'
    match = re.search(pattern, content, re.IGNORECASE)
    if not match:
        return ""

    start = max(0, match.start() - context_chars)
    end = min(len(content), match.end() + context_chars)

    snippet = content[start:end].replace("\n", " ")
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(content) else ""

    return f"{prefix}{snippet}{suffix}"


@router.post("/pages", response_model=PageStatus)
async def create_page(
    create: PageCreate,
    write_queue=Depends(get_write_queue),
) -> PageStatus:
    """Create new page via Write Queue.

    All mutations flow through Write Queue for durability.
    """
    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp

    op_id = str(uuid.uuid4())

    # Normalize the slug so the page lands at ``<slug>.md`` on disk. The wiki
    # repository's list_pages() globs ``*.md``, so a bare slug ("my-page")
    # would be written to a file with no extension and never appear in the
    # page list — and the frontend queryKey namespace would split between
    # bare slugs (from create) and ``.md`` slugs (from list / workflow
    # broadcasts), breaking real-time invalidation. Returning the normalized
    # slug keeps create → list → get → page_updated all on the same key.
    raw_slug = (create.slug or "").strip()
    slug = raw_slug if raw_slug.endswith(".md") else f"{raw_slug}.md" if raw_slug else f"concepts/{op_id}.md"

    ops = [
        WriteOp(
            op_id=op_id,
            session_id="web-api",
            sink_name="wiki",
            payload={
                "op": "create",
                "slug": slug,
                "title": create.title,
                "content": create.content,
                "tags": create.tags,
                "type": create.type,
                "entity_type": create.entity_type,
                "properties": create.properties,
            },
            status=WriteOpStatus.PENDING,
        ),
    ]

    write_queue.enqueue_atomic(ops)

    return PageStatus(
        status="queued",
        slug=slug,
        op_id=op_id,
    )
