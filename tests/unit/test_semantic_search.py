"""Tests for semantic search mode (F-N-2, AC-SEM-1 / AC-SEM-3, AC-FB-1 / AC-FB-2).

v1.12.0 (F-Q-4): removed ``importorskip("sentence_transformers")`` — tests now
mock ``litellm.embedding`` to return fixed vectors. No local ST or torch.
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
    from saw.engines.query.compare import CompareEngine
    from saw.engines.query.compiler import ContextCompiler
    from saw.engines.query.engine import QueryEngine
    from saw.engines.query.graph_traverse import GraphTraverse
    from saw.engines.query.search import FTS5Search
    from saw.engines.query.tree_mode import TreeModeSearch
    from saw.adapters.storage.wiki_repository import WikiRepository
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


def test_sem_ac1_returns_semantic_results(monkeypatch):
    """AC-SEM-1 / AC-FB-2: semantic search returns results ranked by similarity.

    Query "artificial intelligence" should return claims about ML/neural
    networks with higher scores than the Ed25519 claim. Uses API mock,
    no local ST needed.
    """
    conn = _make_db_with_claims(monkeypatch)
    engine = _make_engine(conn)

    result = engine.query(
        question="artificial intelligence", mode="semantic", limit=10
    )

    assert result.mode == "semantic"
    assert len(result.sources) > 0
    assert result.meta.get("semantic_fallback") is False

    # ML claim (c1) should rank higher than Ed25519 (c3)
    doc_ids = [s.get("claim_uuid") for s in result.sources]
    if "c3" in doc_ids and "c1" in doc_ids:
        assert doc_ids.index("c1") < doc_ids.index("c3")

    # Scores should be in descending order
    scores = [s.get("score", 0) for s in result.sources]
    assert scores == sorted(scores, reverse=True)


def test_sem_ac3_empty_index(monkeypatch):
    """AC-SEM-3: empty embedding index returns empty results + index_empty."""
    _setup_mock_api(monkeypatch)

    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    engine = _make_engine(conn)

    result = engine.query(
        question="anything", mode="semantic", limit=10
    )

    assert result.mode == "semantic"
    assert len(result.sources) == 0
    assert result.meta.get("index_empty") is True


def test_sem_fb1_st_fallback(monkeypatch):
    """AC-FB-1: API unavailable + ST available → semantic search works via ST.

    Mocks _api_embedding_available()=False + _st_available()=True to simulate
    the ST fallback path. No actual ST import — _embed_via_st is mocked.
    """
    import saw.adapters.embeddings as emb_mod

    # Don't set up API mock — simulate API unavailable
    monkeypatch.setattr(emb_mod, "_embedding_settings", False)
    monkeypatch.setattr(emb_mod, "_ST_available", True)

    # Mock _embed_via_st to return fixed vectors
    def mock_st_embed(texts):
        return [_topic_vec(t) for t in texts]

    monkeypatch.setattr(emb_mod, "_embed_via_st", mock_st_embed)

    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)

    claims_data = [
        ("c1", "Machine learning is a subset of artificial intelligence."),
        ("c2", "Neural networks are inspired by biological brains."),
    ]
    conn.executemany(
        "INSERT INTO claim (uuid, content, source_uuid, content_hash, workspace_id) "
        "VALUES (?, ?, 'src', 'hash', 'default')",
        claims_data,
    )
    conn.commit()

    # Store embeddings via mocked ST path
    vecs = emb_mod.embed_texts([c[1] for c in claims_data])
    assert vecs is not None
    for (doc_id, _), vec in zip(claims_data, vecs):
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, dim, workspace_id) "
            "VALUES (?, 'claim', 'all-MiniLM-L6-v2', ?, ?, 'default')",
            (doc_id, blob, dim),
        )
    conn.commit()

    engine = _make_engine(conn)
    result = engine.query(
        question="artificial intelligence", mode="semantic", limit=10
    )

    assert result.mode == "semantic"
    assert len(result.sources) > 0
    assert result.meta.get("semantic_fallback") is False


def test_sem_fb2_no_st_api(monkeypatch):
    """AC-FB-2: no ST, API available → semantic search works via API.

    Mocks _st_available()=False + API mock to verify the API path works
    without local ST.
    """
    _setup_mock_api(monkeypatch)

    import saw.adapters.embeddings as emb_mod
    monkeypatch.setattr(emb_mod, "_ST_available", False)

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

    texts = [c[1] for c in claims_data]
    vecs = embed_texts(texts)
    assert vecs is not None
    assert emb_mod._st_available() is False  # ST not available

    for (doc_id, _), vec in zip(claims_data, vecs):
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, dim, workspace_id) "
            "VALUES (?, 'claim', ?, ?, ?, 'default')",
            (doc_id, _MOCK_MODEL, blob, dim),
        )
    conn.commit()

    engine = _make_engine(conn)
    result = engine.query(
        question="artificial intelligence", mode="semantic", limit=10
    )

    assert result.mode == "semantic"
    assert len(result.sources) > 0
    assert result.meta.get("semantic_fallback") is False
