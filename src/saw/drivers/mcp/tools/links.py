"""MCP tools for wiki link operations.

Manages [[wiki-links]] between pages.
"""
from __future__ import annotations

from typing import Any

from saw.drivers.mcp.server import mcp

# Global references (set during initialization)
_wiki_repo = None
_write_queue = None


def init_links_tools(wiki_repo, write_queue) -> None:
    """Initialize links tools with engine references.

    Args:
        wiki_repo: WikiRepository instance.
        write_queue: SQLiteWriteQueue instance.
    """
    global _wiki_repo, _write_queue
    _wiki_repo = wiki_repo
    _write_queue = write_queue


@mcp.tool
async def saw_wiki_link(source_slug: str, target_slug: str) -> dict[str, Any]:
    """Add a [[wiki-link]] from one page to another.

    Appends [[target_slug]] to the source page content.

    Args:
        source_slug: Page that will contain the link.
        target_slug: Page being linked to.

    Returns:
        Status of the operation.
    """
    if not _wiki_repo:
        return {"error": "Wiki repository not initialized"}

    page = _wiki_repo.read(source_slug)
    if not page:
        return {"error": f"Source page '{source_slug}' not found"}

    # Check if link already exists
    if f"[[{target_slug}]]" in page.content:
        return {"status": "exists", "message": "Link already present"}

    # Append link
    new_content = page.content.rstrip() + f"\n\n[[{target_slug}]]\n"

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
                "slug": source_slug,
                "content": new_content,
            },
            status=WriteOpStatus.PENDING,
        ),
    ]

    _write_queue.enqueue_atomic(ops)

    return {
        "status": "queued",
        "source": source_slug,
        "target": target_slug,
        "op_id": op_id,
    }


@mcp.tool
async def saw_wiki_unlink(source_slug: str, target_slug: str) -> dict[str, Any]:
    """Remove a [[wiki-link]] from a page.

    Args:
        source_slug: Page containing the link.
        target_slug: Link target to remove.

    Returns:
        Status of the operation.
    """
    if not _wiki_repo:
        return {"error": "Wiki repository not initialized"}

    page = _wiki_repo.read(source_slug)
    if not page:
        return {"error": f"Source page '{source_slug}' not found"}

    # Remove link pattern
    link_pattern = f"[[{target_slug}]]"
    if link_pattern not in page.content:
        return {"status": "not_found", "message": "Link not found in page"}

    new_content = page.content.replace(link_pattern, "").strip()

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
                "slug": source_slug,
                "content": new_content,
            },
            status=WriteOpStatus.PENDING,
        ),
    ]

    _write_queue.enqueue_atomic(ops)

    return {
        "status": "queued",
        "source": source_slug,
        "target": target_slug,
        "op_id": op_id,
    }


@mcp.tool
async def saw_backlinks(slug: str) -> list[dict[str, Any]]:
    """Get all pages that link to this page.

    Args:
        slug: Target page slug.

    Returns:
        List of pages linking to this page with context snippets.
    """
    if not _wiki_repo:
        return []

    from saw.engines.query.wiki_links import parse_wiki_links

    backlinks = []
    target_slug = slug.strip("/")

    for page_slug in _wiki_repo.list_pages():
        if page_slug == slug:
            continue

        page = _wiki_repo.read(page_slug)
        if not page:
            continue

        links = parse_wiki_links(page.content)
        matching = [l for l in links if l.target == target_slug]

        if matching:
            # Extract context snippet
            import re
            pattern = rf'\[\[{re.escape(target_slug)}[^]]*\]\]'
            match = re.search(pattern, page.content, re.IGNORECASE)
            context = ""
            if match:
                start = max(0, match.start() - 60)
                end = min(len(page.content), match.end() + 60)
                context = page.content[start:end].replace("\n", " ")

            backlinks.append({
                "slug": page_slug,
                "title": page.title,
                "context": context,
                "link_count": len(matching),
            })

    return backlinks


@mcp.tool
async def saw_outlinks(slug: str) -> list[dict[str, Any]]:
    """Get all pages this page links to.

    Args:
        slug: Source page slug.

    Returns:
        List of pages this page links to.
    """
    if not _wiki_repo:
        return []

    page = _wiki_repo.read(slug)
    if not page:
        return []

    from saw.engines.query.wiki_links import parse_wiki_links

    links = parse_wiki_links(page.content)
    outlinks = []

    for link in links:
        target_page = _wiki_repo.read(link.target)
        outlinks.append({
            "target": link.target,
            "alias": link.alias,
            "section": link.section,
            "exists": target_page is not None,
        })

    return outlinks
