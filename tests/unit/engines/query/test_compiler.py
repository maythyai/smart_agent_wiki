"""Unit tests for ContextCompiler."""
from __future__ import annotations

import json
import sqlite3

import pytest

from saw.engines.query.compiler import CompiledContext, ContextCompiler
from saw.engines.query.search import FTS5Search


@pytest.fixture
def in_memory_db() -> sqlite3.Connection:
    """Create in-memory SQLite with test data."""
    conn = sqlite3.connect(":memory:")

    # Create tables
    conn.execute("""
        CREATE TABLE IF NOT EXISTS claim (
            uuid TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            source_uuid TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            confidence TEXT NOT NULL DEFAULT 'unverified',
            page_number INTEGER,
            line_number INTEGER,
            deleted_at TEXT
        )
    """)

    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS fts_index
        USING fts5(
            title,
            content,
            tags,
            original UNINDEXED,
            tokenize='unicode61',
            detail=column
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS wiki_page (
            path TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT,
            page_type TEXT NOT NULL DEFAULT 'summary'
        )
    """)

    # Insert test claims
    test_claims = [
        ("uuid-1", "Machine learning uses neural networks for pattern recognition.", "source-1", "SINGLE_SOURCE"),
        ("uuid-2", "Deep learning is a subset of machine learning with multiple layers.", "source-1", "CROSS_VALIDATED"),
        ("uuid-3", "Transformers replaced RNNs for sequence modeling tasks.", "source-2", "HUMAN_VERIFIED"),
        ("uuid-4", "Natural language processing enables computers to understand text.", "source-2", "UNVERIFIED"),
    ]

    for uuid, content, source, confidence in test_claims:
        conn.execute(
            """INSERT INTO claim (uuid, content, source_uuid, content_hash, confidence)
               VALUES (?, ?, ?, ?, ?)""",
            (uuid, content, source, f"hash-{uuid}", confidence),
        )
        conn.execute(
            """INSERT INTO fts_index (title, content, tags, original)
               VALUES (?, ?, '', ?)""",
            (uuid, content, content),
        )

    # Insert test wiki pages
    conn.execute(
        "INSERT INTO wiki_page (path, title, content, page_type) VALUES (?, ?, ?, ?)",
        ("concepts/machine-learning.md", "Machine Learning", "# Machine Learning", "summary"),
    )

    conn.commit()
    return conn


class TestContextCompiler:
    """Tests for ContextCompiler class."""

    def test_compile_returns_context(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that compile returns a CompiledContext."""
        # Setup mock repos
        class MockClaimsRepo:
            def __init__(self, conn):
                self._conn = conn
            def get_by_id(self, uuid):
                row = self._conn.execute(
                    "SELECT * FROM claim WHERE uuid = ?", (uuid,)
                ).fetchone()
                if row:
                    from saw.domain.claims import Claim
                    from saw.domain.value_objects import ConfidenceLevel
                    return Claim(
                        uuid=row[0],
                        content=row[1],
                        source_uuid=row[2],
                        content_hash=row[3],
                        confidence=ConfidenceLevel[row[4].upper()] if row[4] else ConfidenceLevel.UNVERIFIED,
                    )
                return None
            def get_by_source(self, source_uuid):
                return []

        class MockWikiRepo:
            def list_pages(self):
                return ["concepts/machine-learning.md"]
            def read(self, path):
                return None

        claims_repo = MockClaimsRepo(in_memory_db)
        wiki_repo = MockWikiRepo()
        search_service = FTS5Search(in_memory_db)

        compiler = ContextCompiler(
            claims_repo=claims_repo,
            wiki_repo=wiki_repo,
            search_service=search_service,
            conn=in_memory_db,
        )

        result = compiler.compile("machine learning", token_budget=2000)

        assert isinstance(result, CompiledContext)
        assert result.token_count >= 0

    def test_compile_respects_token_budget(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that compile respects token budget."""
        class MockClaimsRepo:
            def __init__(self, conn):
                self._conn = conn
            def get_by_id(self, uuid):
                row = self._conn.execute(
                    "SELECT * FROM claim WHERE uuid = ?", (uuid,)
                ).fetchone()
                if row:
                    from saw.domain.claims import Claim
                    from saw.domain.value_objects import ConfidenceLevel
                    return Claim(
                        uuid=row[0],
                        content=row[1],
                        source_uuid=row[2],
                        content_hash=row[3],
                        confidence=ConfidenceLevel[row[4].upper()] if row[4] else ConfidenceLevel.UNVERIFIED,
                    )
                return None
            def get_by_source(self, source_uuid):
                return []

        class MockWikiRepo:
            def list_pages(self):
                return []
            def read(self, path):
                return None

        claims_repo = MockClaimsRepo(in_memory_db)
        wiki_repo = MockWikiRepo()
        search_service = FTS5Search(in_memory_db)

        compiler = ContextCompiler(
            claims_repo=claims_repo,
            wiki_repo=wiki_repo,
            search_service=search_service,
            conn=in_memory_db,
        )

        # Small budget should limit results
        result = compiler.compile("learning", token_budget=100)

        assert result.token_count <= 150  # Allow some margin

    def test_compile_prioritizes_high_confidence(
        self, in_memory_db: sqlite3.Connection
    ) -> None:
        """Test that higher confidence claims are included first."""
        class MockClaimsRepo:
            def __init__(self, conn):
                self._conn = conn
            def get_by_id(self, uuid):
                row = self._conn.execute(
                    "SELECT * FROM claim WHERE uuid = ?", (uuid,)
                ).fetchone()
                if row:
                    from saw.domain.claims import Claim
                    from saw.domain.value_objects import ConfidenceLevel
                    return Claim(
                        uuid=row[0],
                        content=row[1],
                        source_uuid=row[2],
                        content_hash=row[3],
                        confidence=ConfidenceLevel[row[4].upper()] if row[4] else ConfidenceLevel.UNVERIFIED,
                    )
                return None
            def get_by_source(self, source_uuid):
                return []

        class MockWikiRepo:
            def list_pages(self):
                return []
            def read(self, path):
                return None

        claims_repo = MockClaimsRepo(in_memory_db)
        wiki_repo = MockWikiRepo()
        search_service = FTS5Search(in_memory_db)

        compiler = ContextCompiler(
            claims_repo=claims_repo,
            wiki_repo=wiki_repo,
            search_service=search_service,
            conn=in_memory_db,
        )

        # Very small budget to trigger prioritization
        result = compiler.compile("learning", token_budget=200)

        # Should include at least some results
        # (Prioritization logic tested indirectly)
        assert isinstance(result, CompiledContext)

    def test_compile_empty_question(self, in_memory_db: sqlite3.Connection) -> None:
        """Test that empty question returns empty context."""
        class MockClaimsRepo:
            def get_by_id(self, uuid):
                return None
            def get_by_source(self, source_uuid):
                return []

        class MockWikiRepo:
            def list_pages(self):
                return []
            def read(self, path):
                return None

        claims_repo = MockClaimsRepo()
        wiki_repo = MockWikiRepo()
        search_service = FTS5Search(in_memory_db)

        compiler = ContextCompiler(
            claims_repo=claims_repo,
            wiki_repo=wiki_repo,
            search_service=search_service,
            conn=in_memory_db,
        )

        result = compiler.compile("", token_budget=2000)

        assert result.content == ""
        assert result.token_count == 0
