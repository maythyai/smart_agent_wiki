"""Semantic search mixin — embedding cosine + ANN path.

Extracted from QueryEngine (S4: engine.py god-file split). The methods are
mixed into :class:`QueryEngine` and rely on the host engine providing:
``effective_workspace_id`` (property), ``_keyword_search`` (fallback),
``_claims_repo``, ``_wiki_repo``, ``_conn``. Logic is unchanged from the
pre-extraction implementation — this is a mechanical move, not a redesign.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class SemanticSearchMixin:
    """Embedding-based semantic search (cosine + ANN).

    Mixed into QueryEngine; accesses engine state via ``self``.
    """

    _ann_index: Any = None  # class-level default; per-instance override

    def _semantic_search(
        self, question: str, limit: int = 20, offset: int = 0
    ) -> Any:  # QueryResult — avoid circular import
        """Semantic search via embedding cosine similarity.

        Returns top-K results ranked by cosine similarity to the query
        embedding. Falls back to BM25 when embeddings unavailable or
        index empty, with ``semantic_fallback`` / ``index_empty`` meta flags.

        Per SPEC-F-N-2 + ADR-010: parallel mode (not fused with BM25).
        Per SPEC-F-O-1 / ADR-011: reuses the F-QS-07 ``QueryCache`` singleton
        with ``mode="semantic"`` key isolation (TTL 300s, cleared on ingest /
        rebuild). Fallback and empty-index results are NOT cached.
        Per SPEC-F-S-1 / ADR-014: cache.get/set conditional on
        ``SAW_SEMANTIC_CACHE_ENABLED``; cache.set skipped below
        ``SAW_SEMANTIC_CACHE_THRESHOLD_MS`` latency threshold.
        """
        import time

        from saw.config.settings import (
            _semantic_cache_enabled,
            _semantic_cache_threshold_ms,
        )
        from saw.engines.query.cache import get_cache

        _cache_enabled = _semantic_cache_enabled()
        _threshold_ms = _semantic_cache_threshold_ms()

        # F-O-1: serve from the query cache before doing any embedding work.
        # T-F-S-1: cache.get is conditional on SAW_SEMANTIC_CACHE_ENABLED.
        _cache = get_cache()
        _cache_params = {
            "limit": limit,
            "offset": offset,
            "mode": "semantic",
            "workspace_id": self.effective_workspace_id,
        }
        if _cache_enabled:
            _cached = _cache.get(question, _cache_params)
            if _cached is not None:
                return _cached

        # 1. Tier check: degrade to BM25 if embeddings unavailable
        from saw.adapters.embeddings import embed_texts, embeddings_available

        if not embeddings_available():
            result = self._keyword_search(question, limit=limit, offset=offset)
            result.mode = "semantic_fallback"
            result.meta = {**(result.meta or {}), "semantic_fallback": True}
            return result

        # 2. Embed query text (timed for threshold check, T-F-S-1)
        _embed_t0 = time.perf_counter()
        vecs = embed_texts([question])
        _embed_latency_ms = (time.perf_counter() - _embed_t0) * 1000
        if vecs is None:
            # Embedding failed (model error) → degrade to BM25
            result = self._keyword_search(question, limit=limit, offset=offset)
            result.mode = "semantic_fallback"
            result.meta = {
                **(result.meta or {}),
                "semantic_fallback": True,
                "embedding_error": True,
            }
            return result
        query_vec = vecs[0]

        # 3. Load all vectors for this workspace from embedding_store
        rows = self._conn.execute(
            "SELECT doc_id, vector, dim FROM embedding_store WHERE workspace_id = ?",
            (self.effective_workspace_id,),
        ).fetchall()

        if not rows:
            # Empty index → return empty result with hint
            from saw.engines.query.engine import QueryResult

            return QueryResult(
                answer="Embedding index is empty. Run `saw rebuild-embeddings` to build it.",
                mode="semantic",
                meta={"semantic_fallback": False, "index_empty": True},
            )

        # 4. Scale-driven search: ANN (hnswlib) for large scale, numpy batch
        #    cosine for small scale; ANN failure → cosine fallback.
        #    T-F-S-2, ADR-014, SPEC-F-S-2.
        ann_threshold = int(os.environ.get("SAW_ANN_THRESHOLD", "500"))
        doc_count = len(rows)
        _ann_meta: dict[str, Any] = {}

        if doc_count > ann_threshold:
            # Try ANN path
            try:
                top_k = self._ann_search(rows, query_vec, limit, offset)
                _ann_meta["ann_search"] = True
            except Exception as ann_exc:
                logger.warning(
                    "ANN search failed, falling back to cosine: %s", ann_exc
                )
                top_k = self._cosine_search_batch(rows, query_vec, limit, offset)
                _ann_meta["ann_fallback"] = True
        else:
            # Small scale → numpy batch cosine
            top_k = self._cosine_search_batch(rows, query_vec, limit, offset)

        # 5. Resolve doc_id → claim/wiki content
        sources: list[dict] = []
        for doc_id, sim in top_k:
            claim = self._claims_repo.get_by_id(
                doc_id, workspace_id=self.effective_workspace_id
            )
            if claim:
                sources.append({
                    "claim_uuid": doc_id,
                    "content": claim.content,
                    "score": round(sim, 4),
                    "type": "claim",
                    "tags": list(claim.tags or []),
                })
            else:
                page = self._wiki_repo.read(doc_id) if self._wiki_repo else None
                if page:
                    sources.append({
                        "page_slug": doc_id,
                        "title": page.title,
                        "content": page.content,
                        "score": round(sim, 4),
                        "type": getattr(page, "entity_type", "wiki"),
                        "tags": list(getattr(page, "tags", []) or []),
                    })

        from saw.engines.query.engine import QueryResult

        _qr = QueryResult(
            answer=(
                f"Found {len(sources)} semantic results for '{question}':\n"
                + "\n".join(
                    f"{i + 1}. {s.get('content', '')[:80]}... "
                    f"(score: {s['score']:.3f})"
                    for i, s in enumerate(sources)
                )
            ),
            sources=sources,
            coverage=100.0,
            mode="semantic",
            meta={
                "total": len(sources),
                "limit": limit,
                "offset": offset,
                "semantic_fallback": False,
                **_ann_meta,
            },
        )
        # F-O-1: cache the result (TTL-bounded; cleared on ingest / rebuild).
        # T-F-S-1: cache.set conditional on SAW_SEMANTIC_CACHE_ENABLED and
        # SAW_SEMANTIC_CACHE_THRESHOLD_MS (skip write when API latency
        # below threshold; cache.get still executes for existing entries).
        try:
            if _cache_enabled and _threshold_ms == 0:
                _cache.set(question, _cache_params, _qr)
            elif _cache_enabled and _threshold_ms > 0:
                if _embed_latency_ms >= _threshold_ms:
                    _cache.set(question, _cache_params, _qr)
            # else: cache disabled → skip set
        except Exception as cache_exc:  # pragma: no cover — best-effort
            logger.warning("semantic cache write failed: %s", cache_exc)
        return _qr

    # ── T-F-S-2: ANN + numpy batch cosine helpers ──────────────────────

    def _cosine_search_batch(
        self,
        rows: list[tuple],
        query_vec: list[float],
        limit: int,
        offset: int,
    ) -> list[tuple[str, float]]:
        """Numpy batch cosine similarity search (T-F-S-2, ADR-014).

        Unpacks all BLOB vectors, computes batch cosine via numpy matrix
        multiply, returns sorted (doc_id, score) pairs.
        """
        import struct

        from saw.adapters.embeddings import batch_cosine_similarity

        doc_ids: list[str] = []
        matrix: list[list[float]] = []
        for doc_id, blob, dim in rows:
            vec = list(struct.unpack(f"<{dim}f", blob))
            doc_ids.append(doc_id)
            matrix.append(vec)
        sims = batch_cosine_similarity(query_vec, matrix)
        scored = list(zip(doc_ids, sims))
        scored.sort(key=lambda x: -x[1])
        return scored[offset : offset + limit]

    def _ann_search(
        self,
        rows: list[tuple],
        query_vec: list[float],
        limit: int,
        offset: int,
    ) -> list[tuple[str, float]]:
        """ANN search via hnswlib index (T-F-S-2, ADR-014).

        Lazy-loads the HNSW index from ``.saw/ann_index_<ws>.bin``;
        builds it from ``embedding_store`` rows if the file is missing.
        Returns sorted (doc_id, score) pairs.
        Raises on failure (caller catches → cosine fallback).
        """
        import struct

        import hnswlib

        index_path = os.path.join(
            ".saw", f"ann_index_{self.effective_workspace_id}.bin"
        )

        # Determine vector dimension from first row
        dim = rows[0][2] if rows else len(query_vec)
        doc_ids = [r[0] for r in rows]

        # Lazy load / build index
        if getattr(self, "_ann_index", None) is None:
            index = hnswlib.Index(space="cosine", dim=dim)
            if os.path.exists(index_path):
                index.load_index(index_path)
            else:
                # Build from rows
                import numpy as np

                vectors = np.array(
                    [list(struct.unpack(f"<{r[2]}f", r[1])) for r in rows],
                    dtype=np.float32,
                )
                index.init_index(max_elements=len(rows), ef_construction=200, M=16)
                index.add_items(vectors, np.arange(len(rows)))
                # Persist for future loads
                os.makedirs(os.path.dirname(index_path), exist_ok=True)
                index.save_index(index_path)
            self._ann_index = index

        # Query top-K (with offset)
        k = min(offset + limit, len(rows))
        labels, distances = self._ann_index.knn_query(
            [query_vec], k=k
        )
        # hnswlib cosine distance = 1 - cosine_similarity
        scored: list[tuple[str, float]] = []
        for i in range(len(labels[0])):
            idx = int(labels[0][i])
            sim = 1.0 - float(distances[0][i])
            scored.append((doc_ids[idx], sim))
        # hnswlib returns by distance ascending (most similar first)
        return scored[offset : offset + limit]
