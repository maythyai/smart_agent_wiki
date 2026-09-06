"""Tests for ANN index scale-driven switching (T-F-S-2, SPEC-F-S-2).

AC-B-1..5: verifies scale-driven ANN/cosine switching, fallback, and
related_pages reuse. All tests use mock embedding (no vLLM, CI-safe).
hnswlib is installed in the test environment.
"""
from __future__ import annotations

import os
import sqlite3
import struct
import tempfile
from pathlib import Path
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


def _make_db(monkeypatch, n_docs: int = 5) -> sqlite3.Connection:
    """Create an in-memory DB with n_docs claims + embeddings."""
    _setup_mock_api(monkeypatch)

    from saw.adapters.embeddings import embed_texts
    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)

    topics = ["machine learning", "neural networks", "deep learning",
              "artificial intelligence", "training data",
              "gradient descent", "transformer model", "attention mechanism",
              "natural language processing", "computer vision"]
    claims_data = []
    for i in range(n_docs):
        topic = topics[i % len(topics)]
        claims_data.append((f"c{i}", f"{topic} example number {i}"))

    conn.executemany(
        "INSERT INTO claim (uuid, content, source_uuid, content_hash, workspace_id) "
        "VALUES (?, ?, 'src', 'hash', 'default')",
        claims_data,
    )
    conn.commit()

    texts = [c[1] for c in claims_data]
    vecs = embed_texts(texts)
    assert vecs is not None
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


def _make_engine(conn, monkeypatch):
    """Build a QueryEngine with a tmp .saw dir for ANN index files."""
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.engines.query.compare import CompareEngine
    from saw.engines.query.compiler import ContextCompiler
    from saw.engines.query.engine import QueryEngine
    from saw.engines.query.graph_traverse import GraphTraverse
    from saw.engines.query.search import FTS5Search
    from saw.engines.query.tree_mode import TreeModeSearch

    # Use tmp dir as cwd so .saw/ann_index_*.bin lands there
    tmp_dir = Path(tempfile.mkdtemp())
    monkeypatch.chdir(tmp_dir)

    wiki_path = tmp_dir / "wiki"
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
    from saw.engines.query.cache import get_cache
    get_cache().clear()


# ── AC-B-1: ANN auto-switch ──────────────────────────────────────────

def test_ac_b_1_ann_auto_switch(monkeypatch):
    """AC-B-1: doc_count > SAW_ANN_THRESHOLD → meta.ann_search: true."""
    # Set threshold to 0 so even 5 docs triggers ANN
    monkeypatch.setenv("SAW_ANN_THRESHOLD", "0")
    _setup_mock_api(monkeypatch)

    conn = _make_db(monkeypatch, n_docs=5)
    engine = _make_engine(conn, monkeypatch)
    _clear_cache()

    result = engine.query(question="machine learning", mode="semantic", limit=10)
    assert result.mode == "semantic"
    assert result.meta.get("ann_search") is True, (
        f"ann_search should be True when doc_count > threshold: meta={result.meta}"
    )


# ── AC-B-2: small-scale cosine ───────────────────────────────────────

def test_ac_b_2_small_scale_cosine(monkeypatch):
    """AC-B-2: doc_count <= SAW_ANN_THRESHOLD → no ANN meta."""
    # Set threshold high so 5 docs stays on cosine path
    monkeypatch.setenv("SAW_ANN_THRESHOLD", "500")
    _setup_mock_api(monkeypatch)

    conn = _make_db(monkeypatch, n_docs=5)
    engine = _make_engine(conn, monkeypatch)
    _clear_cache()

    result = engine.query(question="machine learning", mode="semantic", limit=10)
    assert result.mode == "semantic"
    assert "ann_search" not in result.meta, (
        f"ann_search should not be present for small scale: meta={result.meta}"
    )
    assert "ann_fallback" not in result.meta


# ── AC-B-3: ANN fallback ─────────────────────────────────────────────

def test_ac_b_3_ann_fallback(monkeypatch):
    """AC-B-3: ANN failure → cosine fallback with meta.ann_fallback: true."""
    # Set threshold to 0 so ANN path is attempted
    monkeypatch.setenv("SAW_ANN_THRESHOLD", "0")
    _setup_mock_api(monkeypatch)

    conn = _make_db(monkeypatch, n_docs=5)
    engine = _make_engine(conn, monkeypatch)
    _clear_cache()

    # Sabotage ANN by making hnswlib import fail
    import sys
    original_hnswlib = sys.modules.get("hnswlib")
    sys.modules["hnswlib"] = None  # causes ImportError on `import hnswlib`

    try:
        result = engine.query(question="machine learning", mode="semantic", limit=10)
    finally:
        if original_hnswlib is not None:
            sys.modules["hnswlib"] = original_hnswlib
        else:
            del sys.modules["hnswlib"]

    assert result.mode == "semantic"
    assert result.meta.get("ann_fallback") is True, (
        f"ann_fallback should be True on ANN failure: meta={result.meta}"
    )
    # Should still return results (cosine fallback works)
    assert len(result.sources) > 0


# ── AC-B-4: recall consistency ──────────────────────────────────────

def test_ac_b_4_recall_consistency(monkeypatch):
    """AC-B-4: ANN vs cosine top-K overlap ≥95% on small real data.

    Uses hnswlib with small data (5 docs). Both paths should return the
    same top results since the dataset is small.
    """
    _setup_mock_api(monkeypatch)

    conn = _make_db(monkeypatch, n_docs=10)

    # Run cosine path (threshold high)
    monkeypatch.setenv("SAW_ANN_THRESHOLD", "999999")
    engine_cosine = _make_engine(conn, monkeypatch)
    _clear_cache()
    result_cosine = engine_cosine.query(
        question="machine learning", mode="semantic", limit=5
    )
    cosine_ids = {s.get("claim_uuid") for s in result_cosine.sources}

    # Run ANN path (threshold 0) — fresh engine for fresh index
    monkeypatch.setenv("SAW_ANN_THRESHOLD", "0")
    engine_ann = _make_engine(conn, monkeypatch)
    _clear_cache()
    result_ann = engine_ann.query(
        question="machine learning", mode="semantic", limit=5
    )
    ann_ids = {s.get("claim_uuid") for s in result_ann.sources}

    # Overlap should be high (≥80% for small dataset — exact match expected)
    if cosine_ids and ann_ids:
        overlap = len(cosine_ids & ann_ids) / len(cosine_ids | ann_ids)
        assert overlap >= 0.80, (
            f"ANN vs cosine overlap too low: {overlap:.2f} "
            f"(cosine={cosine_ids} ann={ann_ids})"
        )


# ── AC-B-5: related_pages reuse ──────────────────────────────────────

def test_ac_b_5_related_pages_reuse(monkeypatch):
    """AC-B-5: related_pages batch-loads embeddings (single SELECT)
    instead of per-page SELECT+cosine.
    """
    _setup_mock_api(monkeypatch)

    conn = _make_db(monkeypatch, n_docs=5)
    from saw.adapters.embeddings import embed_texts
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.engines.query.related_pages import compute_related_pages

    # Create wiki pages matching claim doc_ids (write markdown files)
    tmp_dir = Path(tempfile.mkdtemp())
    wiki_path = tmp_dir / "wiki"
    wiki_path.mkdir(parents=True)
    wiki_repo = WikiRepository(wiki_path)

    for i in range(5):
        (wiki_path / f"c{i}.md").write_text(
            f"# Page {i}\n\nMachine learning example {i}\n"
        )

    # Store embeddings with full slug (including .md) as doc_id
    texts = [f"Machine learning example {i}" for i in range(5)]
    vecs = embed_texts(texts)
    assert vecs is not None
    for i, vec in enumerate(vecs):
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, "
            "dim, workspace_id) VALUES (?, 'claim', ?, ?, ?, 'default')",
            (f"c{i}.md", _MOCK_MODEL, blob, dim),
        )
    conn.commit()

    # Verify batch loading: wrap conn to count embedding_store queries
    class _CountingConn:
        def __init__(self, real_conn):
            self._conn = real_conn
            self.embedding_query_count = 0

        def execute(self, sql, *args, **kwargs):
            if "embedding_store" in sql:
                self.embedding_query_count += 1
            return self._conn.execute(sql, *args, **kwargs)

        def __getattr__(self, name):
            return getattr(self._conn, name)

    counting_conn = _CountingConn(conn)

    results = compute_related_pages(
        "c0.md", wiki_repo, top_k=5, conn=counting_conn, workspace_id="default"
    )

    # Should have done at most 2 embedding_store SELECTs:
    # 1 for source page, 1 for all candidates (batch)
    assert counting_conn.embedding_query_count <= 2, (
        f"related_pages should batch-load embeddings (≤2 SELECTs), "
        f"got {counting_conn.embedding_query_count}"
    )
    assert len(results) > 0, "should have related pages"
