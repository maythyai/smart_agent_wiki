"""Workspace full-query-path routing tests — T-F-Z-7 (AC-WS-3).

Verifies that claims scoped to workspace A are not surfaced when the
QueryEngine / claims repo reads with workspace_id=B. Covers the repo
layer (search/get_by_id) and the engine search path (citation resolution).
"""
from __future__ import annotations

import sqlite3
from unittest.mock import MagicMock

import pytest

from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
from saw.db.migrations import apply_migrations
from saw.domain.claims import Claim
from saw.domain.value_objects import ConfidenceLevel, SourceMark


def _make_claim(uuid: str, content: str = "alpha workspace secret") -> Claim:
    import hashlib

    return Claim(
        uuid=uuid,
        content=content,
        source_uuid="src-1",
        page_number=1,
        line_number=1,
        timestamp="2026-09-03T00:00:00Z",
        confidence=ConfidenceLevel.CROSS_VALIDATED,
        source_mark=SourceMark.EXTRACTED,
        tags=["secret"],
        entities=["alpha"],
        content_hash=hashlib.sha256(content.encode()).hexdigest(),
    )


@pytest.fixture()
def repo():
    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    r = SQLiteClaimsRepository(conn)
    # Seed: one claim in workspace "alpha".
    c = _make_claim("claim-alpha-1")
    r.insert(c)
    r.set_workspace("claim-alpha-1", "alpha")
    yield r, conn
    conn.close()


# ── repo layer ───────────────────────────────────────────────────────

def test_get_by_id_filters_cross_workspace(repo):
    """AC-WS-3: get_by_id with a foreign workspace returns None."""
    r, _ = repo
    assert r.get_by_id("claim-alpha-1") is not None  # no filter = visible
    assert r.get_by_id("claim-alpha-1", workspace_id="alpha") is not None
    assert r.get_by_id("claim-alpha-1", workspace_id="beta") is None


def test_search_filters_cross_workspace(repo):
    """AC-WS-3: search with a foreign workspace returns no matches."""
    r, conn = repo
    # Seed the FTS index so search has something to MATCH.
    conn.execute(
        "INSERT INTO fts_index (title, content, tags, original) VALUES (?, ?, ?, ?)",
        ("claim-alpha-1", "alpha workspace secret", "secret", "alpha workspace secret"),
    )
    conn.commit()

    hits_alpha = r.search("alpha", workspace_id="alpha")
    hits_beta = r.search("alpha", workspace_id="beta")
    assert len(hits_alpha) == 1
    assert len(hits_beta) == 0  # cross-workspace search returns nothing


# ── engine layer (search path) ──────────────────────────────────────

def test_engine_keyword_search_excludes_cross_workspace_claims(repo):
    """AC-WS-3: QueryEngine(workspace_id='beta') does not surface alpha claims."""
    from saw.engines.query.engine import QueryEngine

    r, conn = repo
    # FTS5Search is mocked: it "finds" the alpha claim's uuid regardless of
    # workspace (the engine's get_by_id is the scope enforcement point).
    fts = MagicMock()
    fts_result = MagicMock()
    fts_result.claim_uuids = ["claim-alpha-1"]
    fts_result.contents = ["alpha workspace secret"]
    fts_result.scores = [0.9]
    fts_result.total = 1
    fts.search.return_value = fts_result

    wiki = MagicMock()
    wiki.read.return_value = None  # not a wiki page

    engine_beta = QueryEngine(
        search=fts, compiler=MagicMock(), graph=MagicMock(),
        compare_engine=MagicMock(), tree_mode=MagicMock(),
        llm=None, claims_repo=r, wiki_repo=wiki, conn=conn,
        workspace_id="beta",
    )
    result_beta = engine_beta._keyword_search("alpha")
    assert all(s.get("claim_uuid") != "claim-alpha-1" for s in result_beta.sources)

    # Same engine in workspace 'alpha' surfaces the claim.
    engine_alpha = QueryEngine(
        search=fts, compiler=MagicMock(), graph=MagicMock(),
        compare_engine=MagicMock(), tree_mode=MagicMock(),
        llm=None, claims_repo=r, wiki_repo=wiki, conn=conn,
        workspace_id="alpha",
    )
    result_alpha = engine_alpha._keyword_search("alpha")
    assert any(s.get("claim_uuid") == "claim-alpha-1" for s in result_alpha.sources)
