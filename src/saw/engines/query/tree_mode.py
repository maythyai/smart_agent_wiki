"""Tree Mode search for hierarchical documents.

Per D-13: Anchor retrieval -> tree walk -> path aggregation.
Works for documents with heading structure parsed from Markdown.
"""
from __future__ import annotations

import re
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
    line: int = 0
    claim_uuids: list[str] = field(default_factory=list)
    children: list[HeadingNode] = field(default_factory=list)


# A Markdown ATX heading: 1-6 '#' + whitespace + title.
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


class TreeModeSearch:
    """Structure-aware search for hierarchical documents.

    Per D-13: Tree Mode for hierarchical documents using:
    1. Anchor retrieval: FTS5 search for query -> matching documents/sections
    2. Tree walk: parse the document's heading hierarchy and locate the
       section(s) matching the query
    3. Path aggregation: return the heading path (root -> section) plus any
       claims that fall inside that section

    F-QS-08: previously built a flat list of claims under a single root and
    claimed it was a tree. This implementation parses real Markdown heading
    levels into a nested tree for wiki-page anchors, and falls back to the
    claim-based path for claim anchors whose source document is unavailable.
    """

    def __init__(
        self,
        wiki_repo: WikiRepository,
        claims_repo: SQLiteClaimsRepository,
        conn: sqlite3.Connection,
    ) -> None:
        self._wiki_repo = wiki_repo
        self._claims_repo = claims_repo
        self._conn = conn
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

        anchors = self._find_anchors(query, limit)
        if not anchors:
            return []

        results: list[SectionPath] = []
        terms = {t.lower() for t in query.split() if len(t) > 2}

        for doc_id, score in anchors:
            # Prefer wiki-page anchors: they have a real Markdown heading
            # structure we can parse.
            page = self._wiki_repo.read(doc_id) if self._wiki_repo else None
            if page is not None and page.content:
                tree = self._parse_heading_tree(page.content)
                if tree is not None:
                    for node in self._find_matching_sections(tree, terms):
                        path = self._path_to_node(tree, node)
                        results.append(SectionPath(
                            path=path,
                            claims=[],
                            relevance_score=score,
                        ))
                        if len(results) >= limit:
                            return results
                    continue  # wiki page handled

            # Fallback: claim anchor (no wiki page / no heading structure).
            claim = self._claims_repo.get_by_id(doc_id)
            if claim is None:
                continue
            heading_tree = self._get_heading_tree(claim.source_uuid)
            if heading_tree is None:
                continue
            anchor_node = self._find_node_with_claim(heading_tree, claim.uuid)
            if anchor_node is None:
                continue
            path_claims = self._collect_path_claims(heading_tree, anchor_node)
            section_path = self._build_section_path(anchor_node)
            if section_path:
                results.append(SectionPath(
                    path=section_path,
                    claims=path_claims,
                    relevance_score=score,
                ))

        return results

    # ── Anchor retrieval ──────────────────────────────────────────────

    def _find_anchors(self, query: str, limit: int) -> list[tuple[str, float]]:
        """Find anchor doc-ids via FTS5 search.

        FTS5 doc-ids are either claim UUIDs (Fts5Sink) or wiki slugs
        (WikiIndexer); both are valid anchors for tree mode.
        """
        from saw.engines.query.search import FTS5Search

        result = FTS5Search(self._conn).search(query, limit=limit)
        return list(zip(result.claim_uuids, result.scores))

    # ── Real heading-tree parsing (F-QS-08) ────────────────────────────

    def _parse_heading_tree(self, content: str) -> HeadingNode | None:
        """Parse Markdown ATX headings into a nested HeadingNode tree.

        Returns the root (level 0) with children, or None if the document
        has no headings (flat -> tree mode does not apply).
        """
        root = HeadingNode(level=0, title="root", line=0)
        stack: list[HeadingNode] = [root]

        for idx, line in enumerate(content.splitlines(), start=1):
            m = _HEADING_RE.match(line)
            if not m:
                continue
            level = len(m.group(1))
            title = m.group(2).strip()
            node = HeadingNode(level=level, title=title, line=idx)

            # Pop until the top of the stack is a shallower heading.
            while len(stack) > 1 and stack[-1].level >= level:
                stack.pop()
            stack[-1].children.append(node)
            stack.append(node)

        if not root.children:
            return None
        return root

    def _find_matching_sections(
        self, tree: HeadingNode, terms: set[str]
    ) -> list[HeadingNode]:
        """Walk the tree and return headings whose title contains a query term."""
        matches: list[HeadingNode] = []

        def walk(node: HeadingNode) -> None:
            if node.title and node.title != "root":
                title_lower = node.title.lower()
                if not terms or any(t in title_lower for t in terms):
                    matches.append(node)
            for child in node.children:
                walk(child)

        walk(tree)
        return matches

    def _path_to_node(self, root: HeadingNode, target: HeadingNode) -> list[str]:
        """Return the list of heading titles from root to target."""
        path: list[str] = []

        def dfs(node: HeadingNode, trail: list[str]) -> bool:
            current = trail + ([node.title] if node.title and node.title != "root" else [])
            if node is target:
                path.extend(current)
                return True
            for child in node.children:
                if dfs(child, current):
                    return True
            return False

        dfs(root, [])
        return path

    # ── Claim-based fallback (source documents without wiki-page access) ─

    def _get_heading_tree(self, source_uuid: str) -> HeadingNode | None:
        """Best-effort heading tree for a claim source.

        Without direct access to the vault source text we cannot parse real
        headings; we group the source's claims under a single root so the
        claim-based path still works. (Wiki-page anchors use the real parser
        above.)
        """
        if source_uuid in self._heading_cache:
            return self._heading_cache[source_uuid]

        claims = self._claims_repo.get_by_source(source_uuid)
        if not claims:
            return None

        root = HeadingNode(level=0, title="root")
        for claim in claims:
            root.claim_uuids.append(claim.uuid)
        self._heading_cache[source_uuid] = root
        return root

    def _find_node_with_claim(
        self, node: HeadingNode, claim_uuid: str
    ) -> HeadingNode | None:
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
        claims: list[Claim] = []
        for uuid in anchor.claim_uuids:
            claim = self._claims_repo.get_by_id(uuid)
            if claim:
                claims.append(claim)

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
        path: list[str] = []
        if node.title and node.title != "root":
            path.append(node.title)
        return path
