"""TreeModeSearch coverage — T-F-J-3 (AC-COV-2).

Exercises the wiki-page heading branch (the main tree path) and the
heading-tree parser via real Markdown content.
"""
from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

from saw.db.migrations import apply_migrations
from saw.engines.query.tree_mode import TreeModeSearch


def _conn():
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    return conn


def test_search_empty_query_returns_empty():
    tree = TreeModeSearch(MagicMock(), MagicMock(), _conn())
    assert tree.search("") == []


def test_search_wiki_page_heading_branch():
    """A wiki anchor with ATX headings yields a SectionPath via the tree."""
    conn = _conn()
    wiki = MagicMock()
    page = MagicMock()
    page.content = (
        "# Python Guide\n\n"
        "## Basics\n\nintro text\n\n"
        "### Variables\n\nassignment\n\n"
        "## Advanced\n\ndecorators\n"
    )
    wiki.read.return_value = page

    tree = TreeModeSearch(wiki, MagicMock(), conn)
    # Anchor resolves to a wiki slug; mock _find_anchors to return it.
    tree._find_anchors = MagicMock(return_value=[("python", 1.0)])
    results = tree.search("python basics", limit=5)
    assert results, "expected at least one SectionPath"
    # The path is a list of heading titles.
    flat = " ".join(results[0].path)
    assert "Python Guide" in flat or "Basics" in flat
    conn.close()


def test_search_no_anchors_returns_empty():
    tree = TreeModeSearch(MagicMock(), MagicMock(), _conn())
    tree._find_anchors = MagicMock(return_value=[])
    assert tree.search("x") == []


def test_parse_heading_tree_flat_returns_none():
    tree = TreeModeSearch(MagicMock(), MagicMock(), _conn())
    assert tree._parse_heading_tree("no headings here, just text") is None


def test_parse_heading_tree_nested():
    tree = TreeModeSearch(MagicMock(), MagicMock(), _conn())
    root = tree._parse_heading_tree("# A\n## A1\n## A2\n# B\n")
    assert root is not None
    titles = [c.title for c in root.children]
    assert titles == ["A", "B"]
    assert [c.title for c in root.children[0].children] == ["A1", "A2"]


def test_search_claim_anchor_no_heading_tree_skips():
    """Claim-anchor fallback with no heading tree → skip (continue)."""
    conn = _conn()
    claims = MagicMock()
    # Claim resolves but heading tree is None → skip.
    claim = MagicMock()
    claim.uuid = "c1"
    claim.source_uuid = "src-1"
    claims.get_by_id.return_value = claim
    wiki = MagicMock()
    wiki.read.return_value = None  # no wiki page → fallback to claim anchor
    tree = TreeModeSearch(wiki, claims, conn)
    tree._find_anchors = MagicMock(return_value=[("c1", 1.0)])
    tree._get_heading_tree = MagicMock(return_value=None)
    assert tree.search("c1") == []
    conn.close()
