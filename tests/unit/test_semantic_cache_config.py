"""Tests for semantic cache threshold configurability (T-F-S-1, SPEC-F-S-1).

AC-A-1..5: verifies SAW_SEMANTIC_CACHE_ENABLED and
SAW_SEMANTIC_CACHE_THRESHOLD_MS env vars control cache behavior.
All tests use mock embedding (no vLLM, CI-safe).
"""
from __future__ import annotations

import sqlite3
import struct
from unittest.mock import MagicMock

_DIM = 1536
_MOCK_MODEL = "text-embedding-3-small"

_ML_KW = {"machine", "learning", "neural", "ai", "artificial",
          "intelligence", "deep", "ml", "training", "network", "data"}
_CRYPTO_KW = {"crypto", "ed25519", "signature", "elliptic", "curve",
              "cryptography", "algorithm", "byte", "signatures"}
_WEB_KW = {"web", "framework", "rest", "api", "html", "server", "building"}


def _topic_vec(text: str) -> list[float]:
    """Return a _DIM-dim vector biased by text topic for cosine ranking."""
    words = set(text.lower().replace(".", "").replace(",", "").split())
    vec = [0.01] * _DIM
    if words & _ML_KW:
        vec[0] = 0.9
        vec[1] = 0.4
    elif words & _CRYPTO_KW:
        vec[0] = -0.8
        vec[2] = 0.5
    elif words & _WEB_KW:
        vec[1] = 0.8
        vec[3] = 0.3
    else:
        vec[0] = 0.5
    return vec


def _mock_embedding_response(**kwargs):
    response = MagicMock()
    texts = kwargs.get("input", [])
    response.data = [
        {"embedding": _topic_vec(t), "index": i}
        for i, t in enumerate(texts)
    ]
    return response


def _setup_mock_api(monkeypatch):
    """Configure env + mock litellm.embedding for a test."""
    import saw.adapters.embeddings as emb_mod

    monkeypatch.setenv("SAW_EMBEDDING_MODEL", _MOCK_MODEL)
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setattr(emb_mod, "_embedding_settings", None)
    monkeypatch.setattr(
        emb_mod.litellm, "embedding", _mock_embedding_response
    )


def _make_db_with_claims(monkeypatch) -> sqlite3.Connection:
    """Create an in-memory DB with migrations + seeded claims + embeddings."""
    _setup_mock_api(monkeypatch)

    from saw.adapters.embeddings import embed_texts
    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)

    claims_data = [
        ("c1", "Machine learning is a subset of artificial intelligence."),
        ("c2", "Neural networks are inspired by biological brains."),
        ("c3", "The Ed25519 algorithm produces 64-byte signatures."),
    ]
    conn.executemany(
        "INSERT INTO claim (uuid, content, source_uuid, content_hash, workspace_id) "
        "VALUES (?, ?, 'src', 'hash', 'default')",
        claims_data,
    )
    conn.commit()

    # Embed and store vectors
    texts = [c[1] for c in claims_data]
    vecs = embed_texts(texts)
    assert vecs is not None, "mock embedding should return vectors"

    for (doc_id, _), vec in zip(claims_data, vecs):
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, dim, workspace_id) "
            "VALUES (?, 'claim', ?, ?, ?, 'default')",
            (doc_id, _MOCK_MODEL, blob, dim),
        )
    conn.commit()
    return conn


def _make_engine(conn):
    """Build a QueryEngine for semantic mode testing."""
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.engines.query.compare import CompareEngine
    from saw.engines.query.compiler import ContextCompiler
    from saw.engines.query.engine import QueryEngine
    from saw.engines.query.graph_traverse import GraphTraverse
    from saw.engines.query.search import FTS5Search
    from saw.engines.query.tree_mode import TreeModeSearch
    import tempfile
    from pathlib import Path

    wiki_path = Path(tempfile.mkdtemp()) / "wiki"
    wiki_path.mkdir(parents=True)

    claims_repo = SQLiteClaimsRepository(conn)
    wiki_repo = WikiRepository(wiki_path)
    search_service = FTS5Search(conn)
    tree_mode = TreeModeSearch(wiki_repo, claims_repo, conn)
    graph = GraphTraverse(conn)
    compare_engine = CompareEngine(claims_repo, wiki_repo)
    compiler = ContextCompiler(claims_repo, wiki_repo, search_service, conn)

    return QueryEngine(
        search=search_service,
        compiler=compiler,
        graph=graph,
        compare_engine=compare_engine,
        tree_mode=tree_mode,
        llm=None,
        claims_repo=claims_repo,
        wiki_repo=wiki_repo,
        conn=conn,
    )


def _clear_cache():
    """Clear the global query cache singleton."""
    from saw.engines.query.cache import get_cache

    get_cache().clear()


# ── AC-A-1: cache disabled ────────────────────────────────────────────

def test_ac_a_1_cache_disabled_no_hits(monkeypatch):
    """AC-A-1: SAW_SEMANTIC_CACHE_ENABLED=false → hits do not increase."""
    monkeypatch.setenv("SAW_SEMANTIC_CACHE_ENABLED", "false")
    _setup_mock_api(monkeypatch)

    conn = _make_db_with_claims(monkeypatch)
    engine = _make_engine(conn)

    _clear_cache()
    from saw.engines.query.cache import get_cache

    cache = get_cache()
    hits_before = cache.stats()["hits"]

    # Run the same semantic query twice
    engine.query(question="machine learning", mode="semantic", limit=10)
    engine.query(question="machine learning", mode="semantic", limit=10)

    hits_after = cache.stats()["hits"]
    assert hits_after == hits_before, (
        f"hits should not increase when cache disabled: "
        f"before={hits_before} after={hits_after}"
    )


# ── AC-A-2: cache enabled (default) ───────────────────────────────────

def test_ac_a_2_cache_enabled_hits_increase(monkeypatch):
    """AC-A-2: no env (default true) → 2nd query hits cache."""
    monkeypatch.delenv("SAW_SEMANTIC_CACHE_ENABLED", raising=False)
    _setup_mock_api(monkeypatch)

    conn = _make_db_with_claims(monkeypatch)
    engine = _make_engine(conn)

    _clear_cache()
    from saw.engines.query.cache import get_cache

    cache = get_cache()

    # 1st query: miss → writes to cache
    engine.query(question="machine learning", mode="semantic", limit=10)
    hits_after_1st = cache.stats()["hits"]

    # 2nd query: should hit cache
    engine.query(question="machine learning", mode="semantic", limit=10)
    hits_after_2nd = cache.stats()["hits"]

    assert hits_after_2nd > hits_after_1st, (
        f"2nd query should increase hits (cache hit): "
        f"after_1st={hits_after_1st} after_2nd={hits_after_2nd}"
    )


# ── AC-A-3: threshold skip write ─────────────────────────────────────

def test_ac_a_3_threshold_skips_cache_write(monkeypatch):
    """AC-A-3: SAW_SEMANTIC_CACHE_THRESHOLD_MS=100 → cache.set skipped when
    API latency < threshold (mock is ~0ms). cache.get still works for
    pre-existing entries.
    """
    monkeypatch.setenv("SAW_SEMANTIC_CACHE_THRESHOLD_MS", "100")
    _setup_mock_api(monkeypatch)

    conn = _make_db_with_claims(monkeypatch)
    engine = _make_engine(conn)

    _clear_cache()
    from saw.engines.query.cache import get_cache

    cache = get_cache()
    size_before = cache.stats()["size"]

    # Query with mock embedding (latency ~0ms < 100ms threshold → no write)
    engine.query(question="machine learning", mode="semantic", limit=10)

    size_after = cache.stats()["size"]
    # Cache size should not increase (write skipped due to threshold)
    assert size_after == size_before, (
        f"cache should not grow when API latency < threshold: "
        f"before={size_before} after={size_after}"
    )

    # Pre-populate cache manually, then verify cache.get still works
    from saw.engines.query.engine import QueryResult

    _qr = QueryResult(answer="cached", mode="semantic")
    cache.set(
        "machine learning",
        {
            "limit": 10,
            "offset": 0,
            "mode": "semantic",
            "workspace_id": "default",
        },
        _qr,
    )
    hits_before = cache.stats()["hits"]
    # 2nd query should hit the manually-cached entry
    engine.query(question="machine learning", mode="semantic", limit=10)
    hits_after = cache.stats()["hits"]
    assert hits_after > hits_before, (
        "cache.get should still hit pre-existing entries even with threshold"
    )


# ── AC-A-4: backward compatibility ────────────────────────────────────

def test_ac_a_4_backward_compatibility(monkeypatch):
    """AC-A-4: no SAW_SEMANTIC_CACHE_* env → behavior matches v1.13.0
    (cache always enabled, get/set execute normally).
    """
    monkeypatch.delenv("SAW_SEMANTIC_CACHE_ENABLED", raising=False)
    monkeypatch.delenv("SAW_SEMANTIC_CACHE_THRESHOLD_MS", raising=False)
    _setup_mock_api(monkeypatch)

    conn = _make_db_with_claims(monkeypatch)
    engine = _make_engine(conn)

    _clear_cache()
    from saw.engines.query.cache import get_cache

    cache = get_cache()
    hits_before = cache.stats()["hits"]

    # Two identical queries → 2nd should hit cache (v1.13.0 behavior)
    engine.query(question="neural networks", mode="semantic", limit=10)
    hits_after_1st = cache.stats()["hits"]

    engine.query(question="neural networks", mode="semantic", limit=10)
    hits_after_2nd = cache.stats()["hits"]

    assert hits_after_2nd > hits_after_1st, (
        f"backward compat: 2nd query should hit cache: "
        f"after_1st={hits_after_1st} after_2nd={hits_after_2nd}"
    )


# ── AC-A-5: keyword cache not affected ───────────────────────────────

def test_ac_a_5_keyword_cache_unaffected(monkeypatch):
    """AC-A-5: SAW_SEMANTIC_CACHE_ENABLED=false → keyword cache
    (mode='search') still works normally.
    """
    monkeypatch.setenv("SAW_SEMANTIC_CACHE_ENABLED", "false")
    _setup_mock_api(monkeypatch)

    conn = _make_db_with_claims(monkeypatch)
    engine = _make_engine(conn)

    _clear_cache()
    from saw.engines.query.cache import get_cache

    cache = get_cache()

    # Two identical keyword queries → 2nd should hit keyword cache
    engine.query(question="machine", mode="search", limit=10)
    hits_after_1st = cache.stats()["hits"]

    engine.query(question="machine", mode="search", limit=10)
    hits_after_2nd = cache.stats()["hits"]

    assert hits_after_2nd > hits_after_1st, (
        f"keyword cache should work even with semantic cache disabled: "
        f"after_1st={hits_after_1st} after_2nd={hits_after_2nd}"
    )
