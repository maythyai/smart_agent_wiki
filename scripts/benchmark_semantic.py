#!/usr/bin/env python3
"""Benchmark: semantic vs BM25 recall + P99 latency + cache hit rate.

Uses REAL vLLM API (qwen_embedding) — no mock.
Run: python scripts/benchmark_semantic.py [--vllm-base http://localhost:8001]

AC-B-1..4 (F-R-2). When vLLM is unreachable the script exits with an
error message (AC-B-4) — it never degrades to mock vectors.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import struct
import sys
import time
from pathlib import Path

# ── Dataset (≤15 docs, 3 topics × 5 docs) ────────────────────────────

_DATASET: list[tuple[str, str, str]] = [
    # (doc_id, content, topic)
    # ML — docs do NOT contain "AI" literally
    ("ml-1", "Machine learning models for prediction.", "ML"),
    ("ml-2", "Training neural networks on large datasets.", "ML"),
    ("ml-3", "Deep learning architectures for vision.", "ML"),
    ("ml-4", "Gradient descent optimization.", "ML"),
    ("ml-5", "Transformer attention mechanism.", "ML"),
    # crypto
    ("crypto-1", "Ed25519 signatures in cryptography.", "crypto"),
    ("crypto-2", "Elliptic curve algorithm for security.", "crypto"),
    ("crypto-3", "Asymmetric encryption keys.", "crypto"),
    ("crypto-4", "Digital signature verification.", "crypto"),
    ("crypto-5", "Hash function collision resistance.", "crypto"),
    # web
    ("web-1", "REST API design patterns.", "web"),
    ("web-2", "FastAPI web framework.", "web"),
    ("web-3", "HTTP server building.", "web"),
    ("web-4", "Frontend backend separation.", "web"),
    ("web-5", "Stateless authentication.", "web"),
]

# Synonym queries (BM25 should miss, semantic should recall)
_QUERIES: list[tuple[str, str, str]] = [
    ("AI", "ML", "ML query synonym — docs don't contain 'AI' literally"),
    ("public key security", "crypto", "crypto synonym query"),
    ("web service architecture", "web", "web synonym query"),
]


def _health_check(vllm_base: str) -> bool:
    """Return True if the vLLM embedding endpoint is reachable."""
    import httpx

    url = vllm_base.rstrip("/") + "/v1/embeddings"
    try:
        resp = httpx.post(
            url,
            json={"model": "qwen_embedding", "input": ["probe"]},
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


def _setup_env(vllm_base: str) -> None:
    """Configure env so embed_texts() uses the vLLM endpoint."""
    os.environ.setdefault("SAW_EMBEDDING_MODEL", "qwen_embedding")
    os.environ.setdefault("EMBEDDING_API_KEY", "dummy")
    os.environ.setdefault("SAW_EMBEDDING_API_BASE", vllm_base.rstrip("/") + "/v1")


def _build_db(tmp_path: Path) -> sqlite3.Connection:
    """Create in-memory DB, seed claims + FTS5 + embedding_store."""
    from saw.adapters.embeddings import embed_texts
    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(str(tmp_path / "bench.db"))
    apply_migrations(conn)

    # Seed claims
    for doc_id, content, _topic in _DATASET:
        conn.execute(
            "INSERT INTO claim (uuid, content, source_uuid, content_hash, "
            "workspace_id) VALUES (?, ?, 'src', 'hash', 'default')",
            (doc_id, content),
        )
        conn.execute(
            "INSERT INTO fts_index (rowid, title, content, tags, original) "
            "VALUES (?, ?, ?, '', ?)",
            (abs(hash(doc_id)) % (2**31), doc_id, content, doc_id),
        )
    conn.commit()

    # Store embeddings via real API
    texts = [c for _, c, _ in _DATASET]
    vecs = embed_texts(texts)
    if vecs is None:
        print("ERROR: embed_texts() returned None — vLLM may not be running.")
        sys.exit(1)

    for (doc_id, _, _), vec in zip(_DATASET, vecs):
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, "
            "dim, workspace_id) VALUES (?, 'claim', 'qwen_embedding', ?, ?, 'default')",
            (doc_id, blob, dim),
        )
    conn.commit()
    return conn


def _bm25_search(conn: sqlite3.Connection, query: str, limit: int = 10) -> list[str]:
    """BM25 (FTS5) search — returns doc_ids."""
    from saw.engines.query.search import FTS5Search

    fts = FTS5Search(conn)
    result = fts.search(query, limit=limit)
    return list(result.claim_uuids) if hasattr(result, "claim_uuids") else []


def _make_query_engine(conn: sqlite3.Connection, tmp_path: Path):
    """Build a QueryEngine for benchmark (production cache path)."""
    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.engines.query.compare import CompareEngine
    from saw.engines.query.compiler import ContextCompiler
    from saw.engines.query.engine import QueryEngine
    from saw.engines.query.graph_traverse import GraphTraverse
    from saw.engines.query.search import FTS5Search
    from saw.engines.query.tree_mode import TreeModeSearch

    wiki_path = tmp_path / "wiki"
    wiki_path.mkdir(parents=True, exist_ok=True)
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


def _semantic_search(conn: sqlite3.Connection, query: str, limit: int = 10,
                     engine=None) -> list[str]:
    """Semantic search via QueryEngine._semantic_search (production cache path).

    T-F-S-3: routes through the production QueryEngine path (cache, ANN,
    numpy cosine) instead of an independent cosine function.
    """
    if engine is not None:
        result = engine._semantic_search(query, limit=limit)
        return [s.get("claim_uuid") or s.get("page_slug", "")
                for s in result.sources]
    # Fallback: independent cosine (for backward compat with tests)
    from saw.adapters.embeddings import cosine_similarity, embed_texts

    qvecs = embed_texts([query])
    if qvecs is None:
        return []
    rows = conn.execute(
        "SELECT doc_id, vector, dim FROM embedding_store WHERE workspace_id = 'default'"
    ).fetchall()
    scored: list[tuple[str, float]] = []
    for doc_id, blob, dim in rows:
        vec = list(struct.unpack(f"<{dim}f", blob))
        sim = cosine_similarity(qvecs[0], vec)
        scored.append((doc_id, sim))
    scored.sort(key=lambda x: -x[1])
    return [d for d, _ in scored[:limit]]


def _measure_p99(fn, query: str, n: int = 100) -> float:
    """Measure P99 latency (seconds) of a query function."""
    from saw.engines.query.cache import get_cache

    latencies: list[float] = []
    cache = get_cache()
    for _ in range(n):
        cache.clear()
        t0 = time.perf_counter()
        fn(query)
        latencies.append(time.perf_counter() - t0)
    latencies.sort()
    p99_idx = min(int(len(latencies) * 0.99), len(latencies) - 1)
    return latencies[p99_idx]


def _measure_cache_hit(engine, query: str) -> dict:
    """Measure real cache hit via QueryEngine._semantic_search + cache.stats().

    T-F-S-3: uses cache.stats().hits counter (not latency comparison).
    """
    from saw.engines.query.cache import get_cache

    cache = get_cache()
    cache.clear()

    # 1st query: miss → writes to cache
    hits_before = cache.stats()["hits"]
    engine._semantic_search(query)
    hits_after_1st = cache.stats()["hits"]

    # 2nd query: should hit cache
    engine._semantic_search(query)
    hits_after_2nd = cache.stats()["hits"]

    return {
        "hits_before": hits_before,
        "hits_after_1st": hits_after_1st,
        "hits_after_2nd": hits_after_2nd,
        "cache_hit": hits_after_2nd > hits_after_1st,
    }


def _measure_ann_vs_cosine(engine, query: str, n: int = 100) -> dict:
    """Measure ANN vs cosine P99 latency (T-F-S-3).

    Forces ANN path (SAW_ANN_THRESHOLD=0) and cosine path (999999).
    """
    # ANN path
    os.environ["SAW_ANN_THRESHOLD"] = "0"
    engine._ann_index = None  # reset index cache
    ann_p99 = _measure_p99(lambda q: engine._semantic_search(q), query, n)

    # Cosine path
    os.environ["SAW_ANN_THRESHOLD"] = "999999"
    cosine_p99 = _measure_p99(lambda q: engine._semantic_search(q), query, n)

    return {
        "ann_p99_ms": round(ann_p99 * 1000, 2),
        "cosine_p99_ms": round(cosine_p99 * 1000, 2),
    }


def _build_synthetic_db(n_docs: int, dim: int = 384) -> sqlite3.Connection:
    """Create a DB with n_docs synthetic random vectors (no real embedding)."""
    import random

    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)

    random.seed(42)
    for i in range(n_docs):
        vec = [random.gauss(0, 1) for _ in range(dim)]
        norm = sum(x * x for x in vec) ** 0.5
        vec = [x / (norm + 1e-12) for x in vec]
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, "
            "dim, workspace_id) VALUES (?, 'claim', 'synthetic', ?, ?, 'default')",
            (f"doc-{i}", blob, dim),
        )
    conn.commit()
    return conn


def _measure_scale_curve(vllm_base: str) -> list[dict]:
    """Measure semantic P99 at different doc scales (T-F-S-3).

    Generates synthetic datasets with random vectors (no real embedding)
    at 100/500/1000/5000 docs. Only P99 measurement uses real vLLM.
    """
    scales = [100, 500, 1000, 5000]
    results: list[dict] = []

    for n_docs in scales:
        try:
            conn = _build_synthetic_db(n_docs)
            import tempfile
            from pathlib import Path

            tmp_path = Path(tempfile.mkdtemp())
            engine = _make_query_engine(conn, tmp_path)

            # Use real vLLM for query embedding only
            sample_query = _QUERIES[0][0]
            p99 = _measure_p99(
                lambda q: engine._semantic_search(q), sample_query, n=50
            )
            results.append({
                "doc_count": n_docs,
                "p99_ms": round(p99 * 1000, 2),
            })
        except Exception as e:
            # Skip this scale on failure, continue others
            print(f"Warning: scale {n_docs} failed: {e}")
            continue
    return results


def run_benchmark(vllm_base: str, tmp_path: Path | None = None) -> dict:
    """Run the full benchmark and return structured results."""
    _setup_env(vllm_base)

    from saw.adapters import embeddings as emb_mod

    # Reset settings cache so new env takes effect
    emb_mod._embedding_settings = None

    if tmp_path is None:
        import tempfile

        tmp_path = Path(tempfile.mkdtemp())

    conn = _build_db(tmp_path)

    # T-F-S-3: build a QueryEngine for production cache + ANN path
    engine = _make_query_engine(conn, tmp_path)

    recall_sem: dict[str, int] = {}
    recall_bm25: dict[str, int] = {}
    query_details: list[dict] = []

    for q, expected_topic, desc in _QUERIES:
        sem_results = _semantic_search(conn, q, limit=10, engine=engine)
        bm25_results = _bm25_search(conn, q, limit=10)

        # Count how many results belong to expected topic
        topic_docs = {
            d for d, _, t in _DATASET if t == expected_topic
        }
        sem_relevant = len(set(sem_results) & topic_docs)
        bm25_relevant = len(set(bm25_results) & topic_docs)

        recall_sem[q] = sem_relevant
        recall_bm25[q] = bm25_relevant
        query_details.append({
            "query": q,
            "expected_topic": expected_topic,
            "description": desc,
            "semantic_recall": sem_relevant,
            "bm25_recall": bm25_relevant,
            "semantic_doc_ids": sem_results[:5],
            "bm25_doc_ids": bm25_results[:5],
        })

    # P99 latency (first query, cache cleared per iteration)
    sample_query = _QUERIES[0][0]
    p99_sem = _measure_p99(lambda q: engine._semantic_search(q), sample_query)
    p99_bm25 = _measure_p99(lambda q: _bm25_search(conn, q), sample_query)

    # T-F-S-3: cache hit via cache.stats().hits (not latency comparison)
    cache_result = _measure_cache_hit(engine, sample_query)

    # T-F-S-3: ANN vs cosine P99 comparison
    ann_vs_cosine = _measure_ann_vs_cosine(engine, sample_query)

    # T-F-S-3: scale latency curve
    scale_curve = _measure_scale_curve(vllm_base)

    avg_sem = sum(recall_sem.values()) / len(recall_sem)
    avg_bm25 = sum(recall_bm25.values()) / len(recall_bm25)

    return {
        "vllm_endpoint": vllm_base,
        "dataset": {
            "topics": 3,
            "docs_per_topic": 5,
            "total_docs": len(_DATASET),
        },
        "recall": {
            "semantic": {**recall_sem, "avg": round(avg_sem, 2)},
            "bm25": {**recall_bm25, "avg": round(avg_bm25, 2)},
        },
        "p99_ms": {
            "semantic": round(p99_sem * 1000, 2),
            "bm25": round(p99_bm25 * 1000, 2),
        },
        "cache": cache_result,
        "ann_vs_cosine": ann_vs_cosine,
        "scale_curve": scale_curve,
        "query_details": query_details,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark: semantic vs BM25 recall + P99 + cache hit rate (real vLLM)"
    )
    parser.add_argument(
        "--vllm-base",
        default="http://localhost:8001",
        help="vLLM base URL (default: http://localhost:8001)",
    )
    args = parser.parse_args()

    # AC-B-4: health check — exit with error if unreachable, never mock
    if not _health_check(args.vllm_base):
        print(
            f"Error: vLLM embedding endpoint at {args.vllm_base} unreachable. "
            "Start vLLM then re-run.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"vLLM endpoint {args.vllm_base} is reachable. Running benchmark...")
    results = run_benchmark(args.vllm_base)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
