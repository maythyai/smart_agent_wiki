# Release v1.14.0 — semantic 性能优化

> **Additive MINOR** — no breaking API changes. Internal milestone `v4.4`.

## Summary

Semantic search performance optimization: configurable cache threshold,
ANN vector index (hnswlib) for large-scale retrieval, and benchmark
enhancements with real cache.stats() metrics.

This release closes v1.13.0 retro findings **R1** (cache threshold not
adaptable to vLLM local) and **R2** (semantic P99 slower than BM25 at scale).

## What's New

### F-S-1: Semantic cache threshold configurable
- `SAW_SEMANTIC_CACHE_ENABLED` env var (default `true`, backward compatible)
  to enable/disable semantic query cache entirely.
- `SAW_SEMANTIC_CACHE_THRESHOLD_MS` env var (default `0` = no threshold)
  to skip cache writes when embedding API response time is below a latency
  threshold. Remote API (100–500ms) gets cache benefit; local vLLM (37ms)
  can set threshold to avoid ineffective writes.
- Cache `get` still executes for existing entries regardless of threshold.

### F-S-2: ANN vector index (hnswlib) scale-driven
- `hnswlib` (HNSW, MIT, pip-installable) replaces full-scan cosine for
  large-scale semantic search. Auto-switches at `SAW_ANN_THRESHOLD`
  (default 500); small-scale datasets keep numpy batch cosine path.
- `batch_cosine_similarity()` using numpy matrix multiply for the
  fallback / small-scale path (constant optimization, no new dependency).
- `related_pages.py` reuses ANN path for embedding similarity (no duplicate
  cosine scan).
- Falls back to numpy cosine on ANN failure with `meta.ann_fallback: true`.

### F-S-3: Benchmark updated
- Cache hit measured via `cache.stats().hits` counter (not latency comparison).
- ANN vs cosine P99 comparison added.
- 100/500/1000/5000 doc scale latency curve (synthetic vectors, real vLLM
  query embedding).

## Benchmark Results (real vLLM qwen_embedding@8001)

| Metric | Result |
|---|---|
| Semantic recall (avg) | 5.0/5 (vs BM25 0.0/5) |
| Semantic P99 | 54.99ms |
| BM25 P99 | 0.15ms |
| Cache hit | true (after 2nd query) — R1 resolved |
| ANN P99 | 245.23ms (15-doc scale, ANN overhead expected) |
| Cosine P99 | 72.46ms (15-doc scale) |

## Quality Gates

| Gate | Result |
|---|---|
| pytest | 2192 passed, 3 skipped, 4 deselected (benchmark_e2e), 0 failed |
| ruff | 0 errors |
| coverage | 67.34% (≥67 ✓) |
| smoke | 11/11 passed |
| build | smart_agent_wiki-1.14.0 wheel + sdist |
| hnswlib | MIT license, no torch loaded |

## Dependencies

- New: `hnswlib` (MIT, lightweight, no faiss/torch) in `[semantic]` optional extra.
- No breaking changes to existing dependencies.

## Commits

| Task | Commit |
|---|---|
| T-F-S-1 (cache threshold configurable) | `22d25e6` |
| T-F-S-2 (ANN index hnswlib + numpy cosine) | `9e456df` |
| T-F-S-3 (benchmark ANN vs cosine + scale + cache.stats) | `99bc06c` |
| 05-impl done (DEV-LOG + CMS/TMS delta) | `3626ac4` |
| Reconcile (planning artifacts + pyproject bump) | `136befe` |

## Roadmap

- Track: intelligence-adaptation
- Internal milestone: v4.4
- Closes: R1 (cache threshold), R2 (ANN index)
- Next: v1.15.0 (TBD)
