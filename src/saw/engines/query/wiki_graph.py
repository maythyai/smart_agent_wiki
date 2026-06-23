"""Wiki page graph builder.

Builds knowledge graph nodes and edges from wiki pages and [[wiki-links]].
This replaces the entity-only graph with real wiki page connections.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING

from saw.engines.query.wiki_links import parse_wiki_links

if TYPE_CHECKING:
    from saw.adapters.storage.wiki_repository import WikiRepository


@dataclass
class WikiNode:
    """Wiki page node in the graph."""
    id: str  # Page slug
    label: str  # Page title
    type: str  # Page type (concept, entity, source, collection)
    confidence: int  # Confidence level (1-4)
    description: str | None  # First 100 chars of content


@dataclass
class WikiEdge:
    """Wiki link edge between pages."""
    id: str
    source: str  # Source page slug
    target: str  # Target page slug
    type: str  # Always "wiki_link"
    weight: float  # 1.0 for now


class WikiGraphBuilder:
    """Builds graph from wiki pages and [[wiki-links]]."""

    def __init__(self, wiki_repo: WikiRepository) -> None:
        """Initialize wiki graph builder.

        Args:
            wiki_repo: Wiki repository to scan.
        """
        self._wiki_repo = wiki_repo

    def build(self, max_nodes: int = 100) -> tuple[list[WikiNode], list[WikiEdge]]:
        """Build graph from all wiki pages.

        Scans all wiki pages, extracts [[wiki-links]], and builds nodes/edges.

        Args:
            max_nodes: Maximum number of nodes to return.

        Returns:
            Tuple of (nodes, edges).
        """
        nodes: list[WikiNode] = []
        edges: list[WikiEdge] = []
        edge_id = 0

        # Scan all wiki pages
        for slug in self._wiki_repo.list_pages()[:max_nodes]:
            page = self._wiki_repo.read(slug)
            if page is None:
                continue

            # Create node
            page_type = page.page_type.name.lower() if page.page_type else "concept"
            confidence = page.confidence.value if page.confidence else 1
            description = page.content[:100] if page.content else None

            nodes.append(WikiNode(
                id=slug,
                label=page.title,
                type=page_type,
                confidence=confidence,
                description=description,
            ))

            # Extract [[wiki-links]] and create edges
            links = parse_wiki_links(page.content)
            for link in links:
                # Only create edge if target page exists (avoid broken links)
                target_page = self._wiki_repo.read(link.target)
                if target_page is not None:
                    edges.append(WikiEdge(
                        id=f"edge-{edge_id}",
                        source=slug,
                        target=link.target,
                        type="wiki_link",
                        weight=1.0,
                    ))
                    edge_id += 1

        return nodes, edges

    def build_subgraph(
        self, root_slug: str, depth: int = 2, max_nodes: int = 50
    ) -> tuple[list[WikiNode], list[WikiEdge]]:
        """Build subgraph starting from a root page (BFS).

        Args:
            root_slug: Starting page slug.
            depth: Traversal depth (default 2).
            max_nodes: Maximum nodes to include.

        Returns:
            Tuple of (nodes, edges) in the subgraph.
        """
        visited: set[str] = set()
        queue: list[tuple[str, int]] = [(root_slug, 0)]
        nodes: list[WikiNode] = []
        edges: list[WikiEdge] = []
        edge_id = 0

        while queue and len(nodes) < max_nodes:
            slug, current_depth = queue.pop(0)

            if slug in visited:
                continue
            visited.add(slug)

            # Read page
            page = self._wiki_repo.read(slug)
            if page is None:
                continue

            # Create node
            page_type = page.page_type.name.lower() if page.page_type else "concept"
            confidence = page.confidence.value if page.confidence else 1
            description = page.content[:100] if page.content else None

            nodes.append(WikiNode(
                id=slug,
                label=page.title,
                type=page_type,
                confidence=confidence,
                description=description,
            ))

            # Extract links and create edges
            links = parse_wiki_links(page.content)
            for link in links:
                # Create edge
                target_page = self._wiki_repo.read(link.target)
                if target_page is not None:
                    edges.append(WikiEdge(
                        id=f"edge-{edge_id}",
                        source=slug,
                        target=link.target,
                        type="wiki_link",
                        weight=1.0,
                    ))
                    edge_id += 1

                    # Add to queue if not visited and within depth
                    if link.target not in visited and current_depth < depth:
                        queue.append((link.target, current_depth + 1))

        return nodes, edges
