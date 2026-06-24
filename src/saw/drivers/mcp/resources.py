"""MCP resources for reading wiki data.

Per MCP spec: Resources are read-only data sources accessible via URIs.
"""
from __future__ import annotations

from typing import Any

from saw.drivers.mcp.server import mcp

# Global references (set during initialization)
_wiki_repo = None
_query_engine = None


def init_resources(wiki_repo, query_engine=None) -> None:
    """Initialize resources with engine references.

    Args:
        wiki_repo: WikiRepository instance.
        query_engine: QueryEngine instance (optional).
    """
    global _wiki_repo, _query_engine
    _wiki_repo = wiki_repo
    _query_engine = query_engine


@mcp.resource("wiki://pages")
async def list_pages_resource() -> list[dict[str, Any]]:
    """List all wiki pages with metadata."""
    if not _wiki_repo:
        return []

    pages = []
    for path in _wiki_repo.list_pages():
        page = _wiki_repo.read(path)
        if page:
            pages.append({
                "slug": path,
                "title": page.title,
                "entity_type": page.entity_type,
                "tags": page.tags,
                "content_preview": page.content[:200] if page.content else "",
            })
    return pages


@mcp.resource("wiki://page/{slug}")
async def read_page_resource(slug: str) -> dict[str, Any] | None:
    """Read a specific wiki page content and frontmatter."""
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


@mcp.resource("wiki://graph")
async def graph_resource() -> dict[str, Any]:
    """Get the full knowledge graph."""
    if not _query_engine:
        return {"nodes": [], "edges": []}

    from saw.engines.query.wiki_graph import WikiGraphBuilder
    builder = WikiGraphBuilder(_wiki_repo)
    return builder.build()


@mcp.resource("wiki://stats")
async def stats_resource() -> dict[str, Any]:
    """Get knowledge base statistics."""
    if not _wiki_repo:
        return {"total_pages": 0, "by_type": {}}

    pages = _wiki_repo.list_pages()
    by_type: dict[str, int] = {}

    for path in pages:
        page = _wiki_repo.read(path)
        if page:
            t = page.entity_type
            by_type[t] = by_type.get(t, 0) + 1

    return {
        "total_pages": len(pages),
        "by_type": by_type,
    }


@mcp.resource("wiki://search/{query}")
async def search_resource(query: str) -> list[dict[str, Any]]:
    """Search the knowledge base."""
    if not _wiki_repo:
        return []

    results = []
    query_lower = query.lower()

    for path in _wiki_repo.list_pages():
        page = _wiki_repo.read(path)
        if not page:
            continue

        # Simple text match
        if query_lower in page.title.lower() or query_lower in page.content.lower():
            results.append({
                "slug": path,
                "title": page.title,
                "entity_type": page.entity_type,
                "snippet": page.content[:150] if page.content else "",
            })

    return results[:20]  # Limit to 20 results
