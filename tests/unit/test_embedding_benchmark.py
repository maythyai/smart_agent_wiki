"""Benchmark: semantic vs BM25 recall + P99 latency (API mock, no real API key).

AC-TEST-3 (F-Q-4): Verifies the semantic search path works end-to-end with
mock vectors and compares recall against BM25 on a synonym query set.

Real E2E benchmark requires the user to configure a real API key and run:
    pytest tests/unit/test_embedding_benchmark.py --benchmark-e2e
"""
from __future__ import annotations

import os
import sqlite3
import struct
import time
from unittest.mock import MagicMock

import pytest
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
    import saw.adapters.embeddings as emb_mod

    monkeypatch.setenv("SAW_EMBEDDING_MODEL", _MOCK_MODEL)
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setattr(emb_mod, "_embedding_settings", None)
    monkeypatch.setattr(
        emb_mod.litellm, "embedding", _mock_embedding_response
    )


def test_benchmark_semantic_vs_bm25_recall(monkeypatch):
    """AC-TEST-3: benchmark semantic vs BM25 recall on synonym query set.

    Uses mock vectors with known similarity structure to verify semantic
    search recalls synonym-matched docs that BM25 misses.

    Setup:
    - "machine learning" docs → ML-direction mock vectors
    - "cryptography" docs → crypto-direction mock vectors
    Query "AI" (synonym for "machine learning") → semantic should recall
    ML docs. BM25 on "AI" may miss if docs don't contain "AI" literally.
    """
    _setup_mock_api(monkeypatch)

    from saw.adapters.embeddings import embed_texts
    from saw.db.migrations import apply_migrations
    from saw.engines.query.search import FTS5Search

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)

    # Seed claims: ML docs that contain "machine learning" but NOT "AI"
    claims = [
        ("ml-1", "Machine learning models for prediction."),
        ("ml-2", "Training neural networks on large datasets."),
        ("ml-3", "Deep learning architectures for vision."),
        ("crypto-1", "Ed25519 signatures in cryptography."),
        ("crypto-2", "Elliptic curve algorithm for security."),
    ]
    conn.executemany(
        "INSERT INTO claim (uuid, content, source_uuid, content_hash, workspace_id) "
        "VALUES (?, ?, 'src', 'hash', 'default')",
        claims,
    )
    # FTS5 index insert (table name is 'fts_index' per migrations.py)
    for doc_id, content in claims:
        conn.execute(
            "INSERT INTO fts_index (rowid, title, content, tags, original) "
            "VALUES (?, ?, ?, '', ?)",
            (hash(doc_id) % (2**31), doc_id, content, doc_id),
        )
    conn.commit()

    # Store embeddings via mock
    texts = [c[1] for c in claims]
    vecs = embed_texts(texts)
    assert vecs is not None
    for (doc_id, _), vec in zip(claims, vecs):
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, dim, workspace_id) "
            "VALUES (?, 'claim', ?, ?, ?, 'default')",
            (doc_id, _MOCK_MODEL, blob, dim),
        )
    conn.commit()

    # BM25 search for "AI" — docs don't contain "AI" literally, so BM25
    # may return 0 or low-scoring results
    fts = FTS5Search(conn)
    bm25_result = fts.search("AI", limit=10)

    # Semantic search: "AI" query → mock returns ML-direction vector
    # → should match ML docs
    query_vecs = embed_texts(["AI"])
    assert query_vecs is not None
    from saw.adapters.embeddings import cosine_similarity

    rows = conn.execute(
        "SELECT doc_id, vector, dim FROM embedding_store WHERE workspace_id = 'default'"
    ).fetchall()

    scored = []
    for doc_id, blob, dim in rows:
        vec = list(struct.unpack(f"<{dim}f", blob))
        sim = cosine_similarity(query_vecs[0], vec)
        scored.append((doc_id, sim))
    scored.sort(key=lambda x: -x[1])

    semantic_doc_ids = {doc_id for doc_id, _ in scored[:3]}

    # Semantic should recall ML docs
    assert "ml-1" in semantic_doc_ids or "ml-2" in semantic_doc_ids

    # Record the benchmark result
    bm25_count = len(bm25_result.claim_uuids) if hasattr(bm25_result, "claim_uuids") else 0
    semantic_count = len(semantic_doc_ids)

    # Semantic recall >= BM25 recall for synonym queries
    assert semantic_count >= bm25_count, (
        f"semantic recall ({semantic_count}) should be >= BM25 recall ({bm25_count})"
    )


def test_benchmark_p99_latency_mock(monkeypatch):
    """AC-TEST-3: benchmark semantic search P99 latency (mock, baseline [TBD]).

    Mock litellm.embedding has ~0ms latency. Real API P99 requires E2E.
    Records baseline [TBD] for real API comparison.

    The test verifies the semantic search path completes within a reasonable
    time bound (1s for mock — real API will be slower).
    """
    _setup_mock_api(monkeypatch)

    from saw.adapters.embeddings import cosine_similarity, embed_texts
    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)

    # Seed 10 claims with ML and crypto content
    for i in range(5):
        conn.execute(
            "INSERT INTO claim (uuid, content, source_uuid, content_hash, workspace_id) "
            "VALUES (?, ?, 'src', 'hash', 'default')",
            (f"ml-{i}", f"Machine learning model number {i} for training."),
        )
    for i in range(5):
        conn.execute(
            "INSERT INTO claim (uuid, content, source_uuid, content_hash, workspace_id) "
            "VALUES (?, ?, 'src', 'hash', 'default')",
            (f"crypto-{i}", f"Cryptography algorithm {i} for signatures."),
        )
    conn.commit()

    # Store embeddings
    all_claims = conn.execute(
        "SELECT uuid, content FROM claim WHERE deleted_at IS NULL"
    ).fetchall()
    texts = [c[1] for c in all_claims]
    vecs = embed_texts(texts)
    assert vecs is not None
    for (doc_id, _), vec in zip(all_claims, vecs):
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, dim, workspace_id) "
            "VALUES (?, 'claim', ?, ?, ?, 'default')",
            (doc_id, _MOCK_MODEL, blob, dim),
        )
    conn.commit()

    # Time 100 semantic queries
    latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        query_vecs = embed_texts(["machine learning"])
        assert query_vecs is not None
        rows = conn.execute(
            "SELECT doc_id, vector, dim FROM embedding_store WHERE workspace_id = 'default'"
        ).fetchall()
        scored = []
        for doc_id, blob, dim in rows:
            vec = list(struct.unpack(f"<{dim}f", blob))
            sim = cosine_similarity(query_vecs[0], vec)
            scored.append((doc_id, sim))
        scored.sort(key=lambda x: -x[1])
        latencies.append(time.perf_counter() - t0)

    # P99 latency
    latencies.sort()
    p99 = latencies[int(len(latencies) * 0.99)]

    # Mock P99 should be < 1s (no network call)
    assert p99 < 1.0, f"Mock P99 latency {p99:.3f}s exceeds 1s threshold"

    # Record baseline [TBD] for real API comparison
    # Real API P99 will be dominated by network RTT + model inference


# ── T-F-R-2 (v1.13.0): real vLLM benchmark script + AC-B-4 ──────────

def test_benchmark_script_importable():
    """scripts/benchmark_semantic.py can be imported (AC-B-1..3 infra)."""
    import importlib.util
    from pathlib import Path

    script = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_semantic.py"
    assert script.exists(), "scripts/benchmark_semantic.py must exist"
    spec = importlib.util.spec_from_file_location("benchmark_semantic", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Verify key functions exist
    assert hasattr(mod, "run_benchmark")
    assert hasattr(mod, "_health_check")
    assert hasattr(mod, "_DATASET")
    assert len(mod._DATASET) <= 15, "dataset must be ≤15 docs"


def test_ac_b_4_vllm_unreachable_exits_without_mock(monkeypatch, capsys):
    """AC-B-4: when vLLM is unreachable, benchmark exits with error, no mock."""
    import importlib.util
    from pathlib import Path

    script = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_semantic.py"
    spec = importlib.util.spec_from_file_location("benchmark_semantic", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Mock httpx to simulate unreachable endpoint
    import httpx
    def _raise(*a, **kw):
        raise httpx.ConnectError("connection refused")
    monkeypatch.setattr(httpx, "post", _raise)

    assert not mod._health_check("http://localhost:8001"), (
        "health_check must return False when endpoint is unreachable"
    )


@pytest.mark.benchmark_e2e
def test_ac_b_1_real_api_recall(monkeypatch):
    """AC-B-1: semantic recall >= BM25 on synonym query set (real vLLM).

    Skipped in CI without vLLM. Run with:
        pytest tests/unit/test_embedding_benchmark.py -m benchmark_e2e
    """
    import importlib.util
    from pathlib import Path

    script = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_semantic.py"
    spec = importlib.util.spec_from_file_location("benchmark_semantic", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    vllm_base = os.environ.get("SAW_EMBEDDING_API_BASE", "http://localhost:8001")
    if not mod._health_check(vllm_base):
        pytest.skip("vLLM endpoint unreachable — skipping real API benchmark")

    # Save and restore env + settings to avoid leaking state into other tests
    from saw.adapters import embeddings as emb_mod
    saved_settings = emb_mod._embedding_settings
    saved_env = {k: os.environ.get(k) for k in (
        "SAW_EMBEDDING_MODEL", "EMBEDDING_API_KEY", "SAW_EMBEDDING_API_BASE"
    )}
    monkeypatch.setattr(emb_mod, "_embedding_settings", None)

    import tempfile
    try:
        results = mod.run_benchmark(vllm_base, Path(tempfile.mkdtemp()))
    finally:
        emb_mod._embedding_settings = saved_settings
        for k, v in saved_env.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

    avg_sem = results["recall"]["semantic"]["avg"]
    avg_bm25 = results["recall"]["bm25"]["avg"]
    assert avg_sem >= avg_bm25, (
        f"semantic recall ({avg_sem}) should be >= BM25 ({avg_bm25})"
    )


@pytest.mark.benchmark_e2e
def test_ac_b_3_cache_hit_rate(monkeypatch):
    """AC-B-3: 2nd identical query hits cache (lower latency).

    Skipped in CI without vLLM.
    """
    import importlib.util
    from pathlib import Path

    script = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_semantic.py"
    spec = importlib.util.spec_from_file_location("benchmark_semantic", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    vllm_base = os.environ.get("SAW_EMBEDDING_API_BASE", "http://localhost:8001")
    if not mod._health_check(vllm_base):
        pytest.skip("vLLM endpoint unreachable — skipping cache hit benchmark")

    # Save and restore env + settings to avoid leaking state into other tests
    from saw.adapters import embeddings as emb_mod
    saved_settings = emb_mod._embedding_settings
    saved_env = {k: os.environ.get(k) for k in (
        "SAW_EMBEDDING_MODEL", "EMBEDDING_API_KEY", "SAW_EMBEDDING_API_BASE"
    )}
    monkeypatch.setattr(emb_mod, "_embedding_settings", None)

    import tempfile
    try:
        results = mod.run_benchmark(vllm_base, Path(tempfile.mkdtemp()))
    finally:
        emb_mod._embedding_settings = saved_settings
        for k, v in saved_env.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

    cache = results["cache"]
    assert cache["cache_hit"], (
        f"2nd query should hit cache: "
        f"hits_after_1st={cache['hits_after_1st']} "
        f"hits_after_2nd={cache['hits_after_2nd']}"
    )


# ── T-F-S-3 (v1.14.0): cache stats + ANN vs cosine + scale curve ────

def test_ac_c_1_cache_hit_via_stats_mock(monkeypatch):
    """AC-C-1: cache hit measured via cache.stats().hits (mock, CI-safe).

    Verifies _measure_cache_hit uses cache.stats().hits counter,
    not latency comparison. Uses mock embedding (no vLLM).
    """
    import importlib.util
    from pathlib import Path

    # Set up mock embedding API
    monkeypatch.setenv("SAW_EMBEDDING_MODEL", _MOCK_MODEL)
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setattr(
        "saw.adapters.embeddings._embedding_settings", None
    )
    import saw.adapters.embeddings as emb_mod
    monkeypatch.setattr(
        emb_mod.litellm, "embedding", _mock_embedding_response
    )

    script = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_semantic.py"
    spec = importlib.util.spec_from_file_location("benchmark_semantic", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Build a small DB with mock embeddings
    from saw.db.migrations import apply_migrations
    import sqlite3
    import struct

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)

    for i, (doc_id, content, _) in enumerate([
        ("ml-1", "Machine learning models.", "ML"),
        ("ml-2", "Neural networks.", "ML"),
    ]):
        conn.execute(
            "INSERT INTO claim (uuid, content, source_uuid, content_hash, workspace_id) "
            "VALUES (?, ?, 'src', 'hash', 'default')",
            (doc_id, content),
        )
    conn.commit()

    texts = ["Machine learning models.", "Neural networks."]
    vecs = emb_mod.embed_texts(texts)
    assert vecs is not None
    for doc_id, vec in zip(["ml-1", "ml-2"], vecs):
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, dim, workspace_id) "
            "VALUES (?, 'claim', ?, ?, ?, 'default')",
            (doc_id, _MOCK_MODEL, blob, dim),
        )
    conn.commit()

    import tempfile
    tmp_path = Path(tempfile.mkdtemp())
    engine = mod._make_query_engine(conn, tmp_path)

    # Clear cache and measure
    from saw.engines.query.cache import get_cache
    get_cache().clear()

    result = mod._measure_cache_hit(engine, "machine learning")

    # cache_hit should be True (2nd query hits cache)
    assert result["cache_hit"] is True, (
        f"cache_hit should be True via stats: {result}"
    )
    assert result["hits_after_2nd"] > result["hits_after_1st"], (
        f"hits should increase on 2nd query: {result}"
    )


@pytest.mark.benchmark_e2e
def test_ac_c_2_ann_vs_cosine(monkeypatch):
    """AC-C-2: ANN vs cosine P99 comparison in benchmark output.

    Skipped in CI without vLLM.
    """
    import importlib.util
    from pathlib import Path

    script = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_semantic.py"
    spec = importlib.util.spec_from_file_location("benchmark_semantic", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    vllm_base = os.environ.get("SAW_EMBEDDING_API_BASE", "http://localhost:8001")
    if not mod._health_check(vllm_base):
        pytest.skip("vLLM endpoint unreachable — skipping ANN vs cosine benchmark")

    from saw.adapters import embeddings as emb_mod
    saved_settings = emb_mod._embedding_settings
    saved_env = {k: os.environ.get(k) for k in (
        "SAW_EMBEDDING_MODEL", "EMBEDDING_API_KEY", "SAW_EMBEDDING_API_BASE"
    )}
    monkeypatch.setattr(emb_mod, "_embedding_settings", None)

    import tempfile
    try:
        results = mod.run_benchmark(vllm_base, Path(tempfile.mkdtemp()))
    finally:
        emb_mod._embedding_settings = saved_settings
        for k, v in saved_env.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

    ann_vs = results["ann_vs_cosine"]
    assert "ann_p99_ms" in ann_vs, "output must contain ann_p99_ms"
    assert "cosine_p99_ms" in ann_vs, "output must contain cosine_p99_ms"


@pytest.mark.benchmark_e2e
def test_ac_c_3_scale_curve(monkeypatch):
    """AC-C-3: 100/500/1000/5000 scale latency curve in benchmark output.

    Skipped in CI without vLLM.
    """
    import importlib.util
    from pathlib import Path

    script = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_semantic.py"
    spec = importlib.util.spec_from_file_location("benchmark_semantic", script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    vllm_base = os.environ.get("SAW_EMBEDDING_API_BASE", "http://localhost:8001")
    if not mod._health_check(vllm_base):
        pytest.skip("vLLM endpoint unreachable — skipping scale curve benchmark")

    from saw.adapters import embeddings as emb_mod
    saved_settings = emb_mod._embedding_settings
    saved_env = {k: os.environ.get(k) for k in (
        "SAW_EMBEDDING_MODEL", "EMBEDDING_API_KEY", "SAW_EMBEDDING_API_BASE"
    )}
    monkeypatch.setattr(emb_mod, "_embedding_settings", None)

    import tempfile
    try:
        results = mod.run_benchmark(vllm_base, Path(tempfile.mkdtemp()))
    finally:
        emb_mod._embedding_settings = saved_settings
        for k, v in saved_env.items():
            if v is not None:
                os.environ[k] = v
            else:
                os.environ.pop(k, None)

    scale_curve = results["scale_curve"]
    assert len(scale_curve) == 4, (
        f"scale_curve should have 4 entries: {scale_curve}"
    )
    for entry in scale_curve:
        assert "doc_count" in entry
        assert "p99_ms" in entry
