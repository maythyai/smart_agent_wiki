"""Tests for semantic search mode (F-N-2, AC-SEM-1 / AC-SEM-3).

Skips when ``sentence_transformers`` is not installed (the ``[learn]`` extra).
"""
import pytest

pytest.importorskip("sentence_transformers")

import sqlite3
import struct


def _make_db_with_claims() -> sqlite3.Connection:
    """Create an in-memory DB with migrations + seeded claims + embeddings."""
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
    if vecs is None:
        pytest.skip("Embedding unavailable despite importorskip")

    for (doc_id, _), vec in zip(claims_data, vecs):
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, dim, workspace_id) "
            "VALUES (?, 'claim', 'all-MiniLM-L6-v2', ?, ?, 'default')",
            (doc_id, blob, dim),
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


def test_sem_ac1_returns_semantic_results():
    """AC-SEM-1: semantic search returns results ranked by similarity.

    Query "artificial intelligence" should return claims about ML/neural
    networks with higher scores than the Ed25519 claim.
    """
    conn = _make_db_with_claims()
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


def test_sem_ac3_empty_index():
    """AC-SEM-3: empty embedding index returns empty results + index_empty."""
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
