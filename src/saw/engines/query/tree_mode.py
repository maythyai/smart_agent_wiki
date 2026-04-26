"""Tree Mode search for hierarchical documents.

Per D-13: Anchor retrieval -> tree walk -> path aggregation.
Works for documents with heading structure parsed by markdown-it-py.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from saw.domain.claims import Claim

if TYPE_CHECKING:
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository


@dataclass
class SectionPath:
    """A section path in a hierarchical document."""
    path: list[str] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    relevance_score: float = 0.0


@dataclass
class HeadingNode:
    """A node in the heading tree."""
    level: int
    title: str
    claim_uuids: list[str] = field(default_factory=list)
    children: list[HeadingNode] = field(default_factory=list)


class TreeModeSearch:
    """Structure-aware search for hierarchical documents.

    Per D-13: Tree Mode for hierarchical documents using:
    1. Anchor retrieval: FTS5 search for query -> matching sections
    2. Tree walk: from anchor heading -> parent/child headings
    3. Path aggregation: collect claims along the path

    Only works for documents with heading structure.
    Falls back to regular search for flat documents.
    """

    def __init__(
        self,
        wiki_repo: WikiRepository,
        claims_repo: SQLiteClaimsRepository,
        conn: sqlite3.Connection,
    ) -> None:
        """Initialize Tree Mode search.

        Args:
            wiki_repo: Wiki repository for page access.
            claims_repo: Claims repository for claim lookup.
            conn: SQLite connection for FTS5 queries.
        """
        self._wiki_repo = wiki_repo
        self._claims_repo = claims_repo
        self._conn = conn

        # Cache of document heading hierarchies
        # Maps claim source_uuid -> heading tree
        self._heading_cache: dict[str, HeadingNode] = {}

    def search(self, query: str, limit: int = 10) -> list[SectionPath]:
        """Execute tree mode search.

        Args:
            query: Search query string.
            limit: Maximum number of anchor sections.

        Returns:
            List of SectionPath objects with claims along the path.
        """
        if not query or not query.strip():
            return []

        # Step 1: Anchor retrieval - FTS5 search for matching claims
        anchors = self._find_anchors(query, limit)
        if not anchors:
            return []

        results: list[SectionPath] = []

        # For each anchor claim, try to build a section path
        for claim in anchors:
            source_uuid = claim.source_uuid

            # Get or build heading tree for this source
            heading_tree = self._get_heading_tree(source_uuid)
            if heading_tree is None:
                # Flat document - skip tree mode
                continue

            # Find the anchor node in the heading tree
            anchor_node = self._find_node_with_claim(heading_tree, claim.uuid)
            if anchor_node is None:
                continue

            # Step 2: Tree walk - collect parent and child claims
            path_claims = self._collect_path_claims(heading_tree, anchor_node)

            # Build section path
            section_path = self._build_section_path(anchor_node)
            if section_path:
                results.append(SectionPath(
                    path=section_path,
                    claims=path_claims,
                    relevance_score=1.0,  # Could compute from bm25 score
                ))

        return results

    def _find_anchors(self, query: str, limit: int) -> list[Claim]:
        """Find anchor claims via FTS5 search.

        Args:
            query: Search query.
            limit: Maximum anchors.

        Returns:
            List of matching Claim objects.
        """
        from saw.engines.query.search import FTS5Search

        search = FTS5Search(self._conn)
        result = search.search(query, limit=limit)

        claims: list[Claim] = []
        for uuid in result.claim_uuids:
            claim = self._claims_repo.get_by_id(uuid)
            if claim:
                claims.append(claim)

        return claims

    def _get_heading_tree(self, source_uuid: str) -> HeadingNode | None:
        """Get or build heading tree for a source document.

        Args:
            source_uuid: Source document UUID.

        Returns:
            Root HeadingNode or None if unavailable.
        """
        if source_uuid in self._heading_cache:
            return self._heading_cache[source_uuid]

        # Try to load heading structure from vault metadata
        # For now, we build a simple linear structure based on claims
        # In full implementation, this would parse markdown-it-py heading info

        claims = self._claims_repo.get_by_source(source_uuid)
        if not claims:
            return None

        # Build a simple tree based on line numbers (approximation)
        # Claims with earlier line numbers are "parents" of later ones
        root = HeadingNode(level=0, title="root")

        for claim in claims:
            # Add claim to root's children (flat structure for now)
            # Real implementation would use heading level from parsed markdown
            root.claim_uuids.append(claim.uuid)

        self._heading_cache[source_uuid] = root
        return root

    def _find_node_with_claim(
        self, node: HeadingNode, claim_uuid: str
    ) -> HeadingNode | None:
        """Find the node containing a specific claim.

        Args:
            node: Root heading node.
            claim_uuid: UUID to find.

        Returns:
            HeadingNode containing the claim or None.
        """
        if claim_uuid in node.claim_uuids:
            return node

        for child in node.children:
            found = self._find_node_with_claim(child, claim_uuid)
            if found:
                return found

        return None

    def _collect_path_claims(
        self, root: HeadingNode, anchor: HeadingNode
    ) -> list[Claim]:
        """Collect claims from anchor and its parent/children.

        Args:
            root: Root of heading tree.
            anchor: Anchor node found by search.

        Returns:
            List of claims in the section path.
        """
        claims: list[Claim] = []

        # Get anchor's claims
        for uuid in anchor.claim_uuids:
            claim = self._claims_repo.get_by_id(uuid)
            if claim:
                claims.append(claim)

        # Get children's claims (descendants)
        def collect_children(node: HeadingNode) -> None:
            for child in node.children:
                for uuid in child.claim_uuids:
                    claim = self._claims_repo.get_by_id(uuid)
                    if claim and claim not in claims:
                        claims.append(claim)
                collect_children(child)

        collect_children(anchor)

        return claims

    def _build_section_path(self, node: HeadingNode) -> list[str]:
        """Build the section path from root to node.

        Args:
            node: Target heading node.

        Returns:
            List of section titles.
        """
        path: list[str] = []

        if node.title and node.title != "root":
            path.append(node.title)

        return path
