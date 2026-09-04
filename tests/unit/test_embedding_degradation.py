"""Degradation tests for embedding features (F-N-4, AC-EMB-2 / AC-SEM-2 / AC-LINK-2).

These tests do NOT use importorskip — they mock ``embeddings_available()``
to False, simulating tier < FULL, and verify graceful degradation without
needing the real ``sentence_transformers`` package.
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch


def _make_db() -> sqlite3.Connection:
    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    return conn


def test_emb_ac2_no_learn_no_error():
    """AC-EMB-2: tier=LIGHTWEIGHT → EmbeddingSink.write() skips silently,
    embedding_store stays empty, no exception."""
    from saw.write_queue.sinks.embedding_sink import EmbeddingSink
    from saw.write_queue.queue import WriteOp

    conn = _make_db()
    sink = EmbeddingSink(conn)

    op = WriteOp(
        op_id="test-op-deg",
        session_id="sess-1",
        sink_name="embedding",
        payload={
            "doc_id": "claim-deg-1",
            "content": "Some content about machine learning.",
            "entity_type": "claim",
            "workspace_id": "default",
        },
    )
    with patch(
        "saw.adapters.embeddings.embeddings_available", return_value=False
    ):
        sink.write(op)  # should not raise

    count = conn.execute(
        "SELECT COUNT(*) FROM embedding_store"
    ).fetchone()[0]
    assert count == 0  # no vectors written


def test_sem_ac2_degrades_to_bm25():
    """AC-SEM-2: semantic search with no embeddings → degrades to BM25
    with semantic_fallback=True in meta."""
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.engines.query.compare import CompareEngine
    from saw.engines.query.compiler import ContextCompiler
    from saw.engines.query.engine import QueryEngine
    from saw.engines.query.graph_traverse import GraphTraverse
    from saw.engines.query.search import FTS5Search
    from saw.engines.query.tree_mode import TreeModeSearch
    from saw.adapters.storage.wiki_repository import WikiRepository

    conn = _make_db()
    wiki_path = Path(tempfile.mkdtemp()) / "wiki"
    wiki_path.mkdir(parents=True)

    claims_repo = SQLiteClaimsRepository(conn)
    wiki_repo = WikiRepository(wiki_path)
    search_service = FTS5Search(conn)
    tree_mode = TreeModeSearch(wiki_repo, claims_repo, conn)
    graph = GraphTraverse(conn)
    compare_engine = CompareEngine(claims_repo, wiki_repo)
    compiler = ContextCompiler(claims_repo, wiki_repo, search_service, conn)

    engine = QueryEngine(
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

    with patch(
        "saw.adapters.embeddings.embeddings_available", return_value=False
    ):
        result = engine.query(
            question="machine learning", mode="semantic", limit=10
        )

    assert result.mode == "semantic_fallback"
    assert result.meta.get("semantic_fallback") is True


def test_link_ac2_no_learn_keeps_3signal():
    """AC-LINK-2: with embeddings unavailable, compute_related_pages
    behaves identically to the 3-signal v1.8.0 path — no embedding
    reason, no exception."""
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.engines.query.related_pages import compute_related_pages

    wiki_dir = Path(tempfile.mkdtemp()) / "wiki"
    wiki_dir.mkdir(parents=True)
    wiki = WikiRepository(wiki_dir)

    (wiki_dir / "page-a.md").write_text(
        "---\ntags: [python]\n---\n# Page A\n\nPython programming content."
    )
    (wiki_dir / "page-b.md").write_text(
        "---\ntags: [python]\n---\n# Page B\n\nMore Python content here."
    )

    conn = _make_db()

    with patch(
        "saw.adapters.embeddings.embeddings_available", return_value=False
    ):
        related = compute_related_pages(
            "page-a.md", wiki, top_k=8, conn=conn, workspace_id="default"
        )

    # Should return results based on 3-signal (shared tag "python")
    assert len(related) > 0

    # No "semantic similarity" reason should appear
    for r in related:
        reasons_str = "; ".join(r.get("reasons", []))
        assert "semantic similarity" not in reasons_str


def test_sem_ac3_empty_index_with_embeddings_unavailable():
    """When embeddings unavailable AND index empty, semantic_fallback
    takes priority (degrades to BM25, not empty result)."""
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.engines.query.compare import CompareEngine
    from saw.engines.query.compiler import ContextCompiler
    from saw.engines.query.engine import QueryEngine
    from saw.engines.query.graph_traverse import GraphTraverse
    from saw.engines.query.search import FTS5Search
    from saw.engines.query.tree_mode import TreeModeSearch
    from saw.adapters.storage.wiki_repository import WikiRepository

    conn = _make_db()
    wiki_path = Path(tempfile.mkdtemp()) / "wiki"
    wiki_path.mkdir(parents=True)

    claims_repo = SQLiteClaimsRepository(conn)
    wiki_repo = WikiRepository(wiki_path)
    search_service = FTS5Search(conn)
    tree_mode = TreeModeSearch(wiki_repo, claims_repo, conn)
    graph = GraphTraverse(conn)
    compare_engine = CompareEngine(claims_repo, wiki_repo)
    compiler = ContextCompiler(claims_repo, wiki_repo, search_service, conn)

    engine = QueryEngine(
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

    with patch(
        "saw.adapters.embeddings.embeddings_available", return_value=False
    ):
        result = engine.query(
            question="anything", mode="semantic", limit=10
        )

    # Should degrade to BM25 (fallback), not return index_empty
    assert result.mode == "semantic_fallback"
    assert result.meta.get("semantic_fallback") is True
    assert not result.meta.get("index_empty")
