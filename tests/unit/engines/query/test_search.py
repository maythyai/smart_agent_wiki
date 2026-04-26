"""Unit tests for FTS5Search service."""
from __future__ import annotations

import sqlite3

import pytest

from saw.engines.query.search import FTS5Search, SearchResult


@pytest.fixture
def in_memory_db() -> sqlite3.Connection:
    """Create in-memory SQLite with FTS5 for testing."""
    conn = sqlite3.connect(":memory:")

    # Create claim table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS claim (
            uuid TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            source_uuid TEXT NOT NULL,
            page_number INTEGER,
            line_number INTEGER,
            timestamp TEXT,
            confidence TEXT NOT NULL DEFAULT 'unverified',
            source_mark TEXT NOT NULL DEFAULT 'extracted',
            tags TEXT NOT NULL DEFAULT '[]',
            entities TEXT NOT NULL DEFAULT '[]',
            content_hash TEXT NOT NULL,
            session_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT,
            deleted_at TEXT
        )
    """)

    # Create FTS5 virtual table with rowid mapping
    # Using content='' (external content) but storing data directly
    # The key is using rowid to link claim and fts_index
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS fts_index
        USING fts5(
            title,
            content,
            tags,
            tokenize='unicode61',
            detail=column
        )
    """)

    conn.commit()
    return conn


@pytest.fixture
def populated_db(in_memory_db: sqlite3.Connection) -> sqlite3.Connection:
    """Populate in-memory DB with test claims."""
    conn = in_memory_db

    # Insert test claims
    test_claims = [
        ("uuid-1", "Machine learning uses neural networks for pattern recognition.", "source-1"),
        ("uuid-2", "Deep learning is a subset of machine learning with multiple layers.", "source-1"),
        ("uuid-3", "Transformers replaced RNNs for sequence modeling tasks.", "source-2"),
        ("uuid-4", "Natural language processing enables computers to understand text.", "source-2"),
        ("uuid-5", "Computer vision applications include image classification and detection.", "source-3"),
    ]

    for uuid, content, source_uuid in test_claims:
        conn.execute(
            """INSERT INTO claim (uuid, content, source_uuid, content_hash)
               VALUES (?, ?, ?, ?)""",
            (uuid, content, source_uuid, f"hash-{uuid}"),
        )
        # Insert into FTS5 index
        conn.execute(
            """INSERT INTO fts_index (title, content, tags)
               VALUES (?, ?, '')""",
            (uuid, content),
        )

    conn.commit()
    return conn


class TestFTS5Search:
    """Tests for FTS5Search class."""

    def test_search_returns_results(self, populated_db: sqlite3.Connection) -> None:
        """Test that search returns matching results."""
        search = FTS5Search(populated_db)
        result = search.search("machine learning")

        assert isinstance(result, SearchResult)
        assert result.total >= 2  # At least 2 claims about machine learning
        assert len(result.claim_uuids) >= 2

    def test_search_bm25_ranking(self, populated_db: sqlite3.Connection) -> None:
        """Test that bm25 ranking orders results by relevance."""
        search = FTS5Search(populated_db)
        result = search.search("learning")

        # Results should be ordered by bm25 score
        assert result.total >= 2
        # Higher scores should come first
        if len(result.scores) >= 2:
            assert result.scores[0] >= result.scores[-1]

    def test_search_with_snippets(self, populated_db: sqlite3.Connection) -> None:
        """Test that search_with_snippets returns highlighted content."""
        search = FTS5Search(populated_db)
        result = search.search_with_snippets("transformers")

        assert result.total >= 1
        assert "uuid-3" in result.claim_uuids

    def test_search_empty_query(self, populated_db: sqlite3.Connection) -> None:
        """Test that empty query returns empty results."""
        search = FTS5Search(populated_db)
        result = search.search("")

        assert result.total == 0
        assert result.claim_uuids == []

    def test_search_no_matches(self, populated_db: sqlite3.Connection) -> None:
        """Test search with no matching results."""
        search = FTS5Search(populated_db)
        result = search.search("xyznonexistent123")

        assert result.total == 0
        assert result.claim_uuids == []

    def test_search_pagination(self, populated_db: sqlite3.Connection) -> None:
        """Test search with limit and offset."""
        search = FTS5Search(populated_db)

        # Get first page
        result1 = search.search("learning", limit=2, offset=0)
        assert len(result1.claim_uuids) <= 2

        # Get second page
        result2 = search.search("learning", limit=2, offset=2)
        # Should have different results (or none if first page got all)
        if result2.claim_uuids:
            assert result1.claim_uuids != result2.claim_uuids

    def test_count_matches(self, populated_db: sqlite3.Connection) -> None:
        """Test count returns total matching results."""
        search = FTS5Search(populated_db)
        count = search.count("learning")

        assert count >= 2

    def test_count_empty_query(self, populated_db: sqlite3.Connection) -> None:
        """Test count with empty query returns 0."""
        search = FTS5Search(populated_db)
        count = search.count("")

        assert count == 0

    def test_search_respects_deleted(self, populated_db: sqlite3.Connection) -> None:
        """Test that deleted claims are excluded from search."""
        conn = populated_db

        # Mark a claim as deleted
        conn.execute(
            "UPDATE claim SET deleted_at = datetime('now') WHERE uuid = 'uuid-1'"
        )
        conn.commit()

        search = FTS5Search(conn)
        result = search.search("machine learning")

        # uuid-1 should not appear in results
        assert "uuid-1" not in result.claim_uuids
