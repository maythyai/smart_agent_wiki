"""MCP tools for page CRUD operations.

All mutations flow through Write Queue for durability.
"""
from __future__ import annotations

from typing import Any

from saw.drivers.mcp.server import mcp

# Global references (set during initialization)
_wiki_repo = None
_write_queue = None


def init_pages_tools(wiki_repo, write_queue) -> None:
    """Initialize pages tools with engine references.

    Args:
        wiki_repo: WikiRepository instance.
        write_queue: SQLiteWriteQueue instance.
    """
    global _wiki_repo, _write_queue
    _wiki_repo = wiki_repo
    _write_queue = write_queue


@mcp.tool
async def saw_page_create(
    slug: str,
    title: str,
    content: str,
    tags: list[str] | None = None,
    entity_type: str = "note",
    properties: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new wiki page via Write Queue.

    Args:
        slug: URL-safe page identifier.
        title: Page title.
        content: Markdown content.
        tags: List of tags.
        entity_type: Entity type (note, person, project, etc.).
        properties: Type-specific structured properties.

    Returns:
        Status with op_id for tracking.
    """
    if not _write_queue:
        return {"error": "Write queue not initialized"}

    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp
    import uuid

    op_id = str(uuid.uuid4())

    ops = [
        WriteOp(
            op_id=op_id,
            session_id="mcp",
            sink_name="wiki",
            payload={
                "op": "create",
                "slug": slug,
                "title": title,
                "content": content,
                "tags": tags or [],
                "entity_type": entity_type,
                "properties": properties or {},
            },
            status=WriteOpStatus.PENDING,
        ),
    ]

    _write_queue.enqueue_atomic(ops)

    return {
        "status": "queued",
        "slug": slug,
        "op_id": op_id,
    }


@mcp.tool
async def saw_page_update(
    slug: str,
    content: str,
    message: str | None = None,
) -> dict[str, Any]:
    """Update an existing wiki page via Write Queue.

    Args:
        slug: Page slug to update.
        content: New Markdown content.
        message: Optional commit message.

    Returns:
        Status with op_id for tracking.
    """
    if not _write_queue:
        return {"error": "Write queue not initialized"}

    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp
    import uuid

    op_id = str(uuid.uuid4())

    ops = [
        WriteOp(
            op_id=op_id,
            session_id="mcp",
            sink_name="wiki",
            payload={
                "op": "write",
                "slug": slug,
                "content": content,
                "message": message,
            },
            status=WriteOpStatus.PENDING,
        ),
        WriteOp(
            op_id=f"{op_id}-index",
            session_id="mcp",
            sink_name="fts5",
            payload={
                "op": "upsert",
                "slug": slug,
                "content": content,
            },
            status=WriteOpStatus.PENDING,
        ),
    ]

    _write_queue.enqueue_atomic(ops)

    return {
        "status": "queued",
        "slug": slug,
        "op_id": op_id,
    }


@mcp.tool
async def saw_page_delete(slug: str, message: str | None = None) -> dict[str, Any]:
    """Delete a wiki page via Write Queue.

    Args:
        slug: Page slug to delete.
        message: Optional deletion reason.

    Returns:
        Status with op_id for tracking.
    """
    if not _write_queue:
        return {"error": "Write queue not initialized"}

    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp
    import uuid

    op_id = str(uuid.uuid4())

    ops = [
        WriteOp(
            op_id=op_id,
            session_id="mcp",
            sink_name="wiki",
            payload={
                "op": "delete",
                "slug": slug,
                "message": message,
            },
            status=WriteOpStatus.PENDING,
        ),
        WriteOp(
            op_id=f"{op_id}-index",
            session_id="mcp",
            sink_name="fts5",
            payload={
                "op": "delete",
                "slug": slug,
            },
            status=WriteOpStatus.PENDING,
        ),
    ]

    _write_queue.enqueue_atomic(ops)

    return {
        "status": "queued",
        "slug": slug,
        "op_id": op_id,
    }


@mcp.tool
async def saw_page_read(slug: str) -> dict[str, Any] | None:
    """Read a wiki page's content and metadata.

    Args:
        slug: Page slug to read.

    Returns:
        Page data or None if not found.
    """
    if not _wiki_repo:
        return None

    page = _wiki_repo.read(slug)
    if not page:
        return None

    return {
        "slug": slug,
        "title": page.title,
        "entity_type": page.entity_type,
        "tags": page.tags,
        "content": page.content,
        "frontmatter": page.frontmatter,
        "properties": page.properties,
    }


@mcp.tool
async def saw_page_list(
    entity_type: str | None = None,
    tag: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List wiki pages with optional filters.

    Args:
        entity_type: Filter by entity type.
        tag: Filter by tag.
        limit: Maximum number of pages to return.

    Returns:
        List of page metadata objects.
    """
    if not _wiki_repo:
        return []

    pages = []
    for path in _wiki_repo.list_pages():
        page = _wiki_repo.read(path)
        if not page:
            continue

        # Apply filters
        if entity_type and page.entity_type != entity_type:
            continue
        if tag and tag not in page.tags:
            continue

        pages.append({
            "slug": path,
            "title": page.title,
            "entity_type": page.entity_type,
            "tags": page.tags,
            "content_preview": page.content[:150] if page.content else "",
        })

        if len(pages) >= limit:
            break

    return pages
