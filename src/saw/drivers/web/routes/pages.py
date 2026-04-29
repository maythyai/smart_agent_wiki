"""Page API endpoints.

Per D-13: GET /api/pages - list all wiki pages.
Per D-14: GET /api/pages/{slug} - get page content.
Per D-15: PUT /api/pages/{slug} - update page via Write Queue.
Per D-16: DELETE /api/pages/{slug} - delete page via Write Queue.

All mutations flow through Write Queue for durability (per ARCHITECTURE.md).
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Path, Request

from saw.drivers.web.schemas.pages import (
    PageCreate,
    PageDelete,
    PageListResponse,
    PageResponse,
    PageStatus,
    PageUpdate,
)

router = APIRouter()


def get_query_engine(request: Request):
    """Dependency: get QueryEngine from app.state."""
    return request.app.state.query


def get_write_queue(request: Request):
    """Dependency: get WriteQueue from app.state."""
    return request.app.state.write_queue


@router.get("/pages", response_model=PageListResponse)
async def list_pages(
    engine=Depends(get_query_engine),
) -> PageListResponse:
    """List all wiki page slugs (per D-13).

    Returns a list of all available wiki page slugs.
    """
    pages: list[str] = []
    if hasattr(engine, "_wiki_repo") and engine._wiki_repo is not None:
        pages = engine._wiki_repo.list_pages()
    elif hasattr(engine, "wiki") and engine.wiki is not None:
        pages = engine.wiki.list_pages()

    return PageListResponse(
        slugs=pages,
        total=len(pages),
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

    ops = [
        WriteOp(
            op_id=op_id,
            session_id="web-api",
            sink_name="wiki",
            payload={
                "op": "create",
                "slug": create.slug,
                "title": create.title,
                "content": create.content,
                "tags": create.tags,
                "type": create.type,
            },
            status=WriteOpStatus.PENDING,
        ),
    ]

    write_queue.enqueue_atomic(ops)

    return PageStatus(
        status="queued",
        slug=create.slug,
        op_id=op_id,
    )
