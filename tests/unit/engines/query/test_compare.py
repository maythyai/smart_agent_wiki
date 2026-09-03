"""CompareEngine coverage — T-F-J-3 (AC-COV-2)."""
from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

import pytest

from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.db.migrations import apply_migrations
from saw.domain.claims import Claim
from saw.domain.value_objects import ConfidenceLevel, SourceMark
from saw.engines.query.compare import CompareEngine, ComparisonResult


def _claim(uuid, source_uuid="src-1", content="shared"):
    import hashlib

    return Claim(
        uuid=uuid, content=content, source_uuid=source_uuid,
        confidence=ConfidenceLevel.CROSS_VALIDATED, source_mark=SourceMark.EXTRACTED,
        tags=[], entities=[], content_hash=hashlib.sha256(content.encode()).hexdigest(),
    )


def test_compare_fewer_than_two_pages():
    from saw.engines.query.compare import ComparisonResult

    engine = CompareEngine(MagicMock(), MagicMock())
    r = engine.compare(["only"])
    assert isinstance(r, ComparisonResult)
    assert r.pages == ["only"]


def test_compare_shared_and_unique():
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    repo = SQLiteClaimsRepository(conn)
    # shared claim (same source) + unique claims per source
    repo.insert(_claim("c-shared", "src-common", "shared"))
    repo.insert(_claim("c-a", "src-a", "unique A"))
    repo.insert(_claim("c-b", "src-b", "unique B"))

    wiki = MagicMock()
    page_a = MagicMock()
    page_a.frontmatter = {"sources": ["src-common", "src-a"]}
    page_b = MagicMock()
    page_b.frontmatter = {"sources": ["src-common", "src-b"]}

    def read(name):
        return {"a": page_a, "b": page_b}.get(name)

    wiki.read.side_effect = read

    engine = CompareEngine(repo, wiki)
    r = engine.compare(["a", "b"])
    assert r.similarity > 0
    assert any(c.uuid == "c-shared" for c in r.shared_claims)
    assert any(c.uuid == "c-a" for c in r.unique_claims.get("a", []))
    conn.close()


def test_get_page_claims_fallback_search_by_title():
    """No frontmatter sources → search claims by page title."""
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    repo = SQLiteClaimsRepository(conn)
    repo.insert(_claim("c1", "src-1", "the topic content"))
    conn.execute(
        "INSERT INTO fts_index (title, content, tags, original) VALUES (?, ?, ?, ?)",
        ("c1", "the topic content", "", "the topic content"),
    )
    conn.commit()

    wiki = MagicMock()
    page = MagicMock()
    page.title = "the topic"
    page.frontmatter = {}
    wiki.read.return_value = page

    engine = CompareEngine(repo, wiki)
    claims = engine._get_page_claims("the topic")
    assert len(claims) >= 1
    conn.close()


def test_get_page_claims_missing_page_returns_empty():
    engine = CompareEngine(MagicMock(), MagicMock())
    # wiki.read returns None for all prefixes
    wiki = MagicMock()
    wiki.read.return_value = None
    engine._wiki_repo = wiki
    assert engine._get_page_claims("nope") == []
