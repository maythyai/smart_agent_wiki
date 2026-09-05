"""Semantic search cache tests (F-O-1, AC-CACHE-1/2/3/4).

All tests use ``unittest.mock.patch`` to mock ``embed_texts`` /
``cosine_similarity`` / ``embeddings_available`` — no dependency on
``sentence_transformers`` (CI-safe).
"""
from __future__ import annotations

import sqlite3
import struct
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


def _make_db() -> sqlite3.Connection:
    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    return conn


def _seed_embedding(conn, doc_id: str, vec, workspace_id: str = "default"):
    """Insert a single embedding row into ``embedding_store``."""
    dim = len(vec)
    blob = struct.pack(f"<{dim}f", *vec)
    conn.execute(
        "DELETE FROM embedding_store WHERE doc_id = ? AND workspace_id = ?",
        (doc_id, workspace_id),
    )
    conn.execute(
        "INSERT INTO embedding_store (doc_id, entity_type, model, vector, dim, workspace_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (doc_id, "claim", "all-MiniLM-L6-v2", blob, dim, workspace_id),
    )
    conn.commit()


def _build_engine(conn, workspace_id: str = "default"):
    """Build a minimal QueryEngine wired for semantic search tests."""
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.engines.query.compare import CompareEngine
    from saw.engines.query.compiler import ContextCompiler
    from saw.engines.query.engine import QueryEngine
    from saw.engines.query.graph_traverse import GraphTraverse
    from saw.engines.query.search import FTS5Search
    from saw.engines.query.tree_mode import TreeModeSearch
    from saw.adapters.storage.wiki_repository import WikiRepository

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
        workspace_id=workspace_id,
    )
    return engine


class TestSemanticCache:
    """AC-CACHE-1/2/3/4: semantic search cache reuse F-QS-07 singleton."""

    def setup_method(self):
        """Clear the global cache singleton before each test."""
        from saw.engines.query.cache import get_cache

        get_cache().clear()

    # ── AC-CACHE-1: cache hit skips embed + cosine ──────────────────

    def test_ac_cache_1_cache_hit_skips_embed(self):
        """First call invokes embed_texts + cosine_similarity; second
        identical call returns the cached result WITHOUT invoking them."""
        conn = _make_db()
        _seed_embedding(conn, "claim-1", [0.1, 0.2, 0.3])
        engine = _build_engine(conn, workspace_id="default")

        # Mock a claim to be returned by claims_repo.get_by_id
        mock_claim = MagicMock()
        mock_claim.content = "Cached semantic content"
        mock_claim.tags = []
        mock_claim.confidence.name = "high"
        engine._claims_repo.get_by_id = MagicMock(return_value=mock_claim)

        with (
            patch(
                "saw.adapters.embeddings.embeddings_available", return_value=True
            ),
            patch(
                "saw.adapters.embeddings.embed_texts",
                return_value=[[0.5, 0.6, 0.7]],
            ) as mock_embed,
            patch(
                "saw.adapters.embeddings.cosine_similarity",
                return_value=0.95,
            ) as mock_cosine,
        ):
            # First call — cache miss, embed/cosine invoked
            r1 = engine.query("test query", mode="semantic", limit=10)
            assert r1.mode == "semantic"
            assert mock_embed.call_count == 1
            assert mock_cosine.call_count == 1

            # Second identical call — cache hit, embed/cosine NOT invoked
            r2 = engine.query("test query", mode="semantic", limit=10)
            assert r2.mode == "semantic"
            # embed_texts / cosine_similarity must NOT have been called again
            assert mock_embed.call_count == 1
            assert mock_cosine.call_count == 1
            # Results are the same cached object
            assert r2.answer == r1.answer

    # ── AC-CACHE-2: workspace isolation ─────────────────────────────

    def test_ac_cache_2_workspace_isolation(self):
        """Cache populated in workspace A is NOT served to workspace B."""
        conn = _make_db()
        _seed_embedding(conn, "claim-a", [0.1, 0.2, 0.3], workspace_id="ws-a")
        _seed_embedding(conn, "claim-b", [0.4, 0.5, 0.6], workspace_id="ws-b")

        engine_a = _build_engine(conn, workspace_id="ws-a")
        engine_b = _build_engine(conn, workspace_id="ws-b")

        mock_claim_a = MagicMock()
        mock_claim_a.content = "Content A"
        mock_claim_a.tags = []
        mock_claim_a.confidence.name = "high"
        engine_a._claims_repo.get_by_id = MagicMock(return_value=mock_claim_a)

        mock_claim_b = MagicMock()
        mock_claim_b.content = "Content B"
        mock_claim_b.tags = []
        mock_claim_b.confidence.name = "medium"
        engine_b._claims_repo.get_by_id = MagicMock(return_value=mock_claim_b)

        embed_calls: list[list[str]] = []

        def _track_embed(texts):
            embed_calls.append(texts)
            return [[0.9, 0.8, 0.7]]

        with (
            patch(
                "saw.adapters.embeddings.embeddings_available", return_value=True
            ),
            patch(
                "saw.adapters.embeddings.embed_texts", side_effect=_track_embed
            ),
            patch(
                "saw.adapters.embeddings.cosine_similarity", return_value=0.9
            ),
        ):
            # Populate cache in workspace A
            engine_a.query("shared query", mode="semantic", limit=10)
            assert len(embed_calls) == 1

            # Same query in workspace B → cache MISS (different workspace_id)
            engine_b.query("shared query", mode="semantic", limit=10)
            assert len(embed_calls) == 2  # embed called for both workspaces

    # ── AC-CACHE-3: cache invalidation on clear() ────────────────────

    def test_ac_cache_3_invalidation_on_clear(self):
        """After ``get_cache().clear()``, a repeat query is a cache miss
        (embed/cosine re-invoked)."""
        from saw.engines.query.cache import get_cache

        conn = _make_db()
        _seed_embedding(conn, "claim-1", [0.1, 0.2, 0.3])
        engine = _build_engine(conn, workspace_id="default")

        mock_claim = MagicMock()
        mock_claim.content = "Content"
        mock_claim.tags = []
        mock_claim.confidence.name = "high"
        engine._claims_repo.get_by_id = MagicMock(return_value=mock_claim)

        with (
            patch(
                "saw.adapters.embeddings.embeddings_available", return_value=True
            ),
            patch(
                "saw.adapters.embeddings.embed_texts",
                return_value=[[0.5, 0.6, 0.7]],
            ) as mock_embed,
            patch(
                "saw.adapters.embeddings.cosine_similarity",
                return_value=0.9,
            ),
        ):
            engine.query("invalidate me", mode="semantic", limit=10)
            assert mock_embed.call_count == 1

            # Clear cache → next call should be a miss
            get_cache().clear()
            engine.query("invalidate me", mode="semantic", limit=10)
            assert mock_embed.call_count == 2  # re-invoked after clear

    # ── AC-CACHE-4: fallback does not write semantic cache ──────────

    def test_ac_cache_4_fallback_not_cached(self):
        """When ``embeddings_available()`` returns False, the search
        degrades to BM25. The semantic cache must NOT grow — the fallback
        result is served from the keyword cache (mode="search"), never
        written to the semantic keyspace (mode="semantic")."""
        from saw.engines.query.cache import QueryCache, get_cache

        conn = _make_db()
        # Seed a claim + FTS row so the keyword fallback returns something
        conn.execute(
            "INSERT INTO claim (uuid, content, source_uuid, content_hash, workspace_id) "
            "VALUES ('claim-fts-1', 'Some keyword content for fallback', "
            "'src-1', 'hash-1', 'default')"
        )
        conn.execute(
            "INSERT INTO fts_index (title, content, tags, original) "
            "VALUES ('claim-fts-1', 'Some keyword content for fallback', '', 'claim-fts-1')"
        )
        conn.commit()

        engine = _build_engine(conn, workspace_id="default")

        cache = get_cache()
        cache.clear()

        # Pre-compute the semantic cache key to check absence after fallback
        sem_params = {
            "limit": 10,
            "offset": 0,
            "mode": "semantic",
            "workspace_id": "default",
        }
        sem_key = cache._make_key("fallback query", sem_params)

        with patch(
            "saw.adapters.embeddings.embeddings_available", return_value=False
        ):
            result = engine.query("fallback query", mode="semantic", limit=10)
            assert result.meta.get("semantic_fallback") is True

        # The semantic keyspace must NOT contain the fallback result
        assert sem_key not in cache._cache, (
            "Fallback result must not be cached in semantic keyspace"
        )
