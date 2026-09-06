# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [v1.14.0] - 2026-09-06
### Added
- `SAW_SEMANTIC_CACHE_ENABLED` env var to enable/disable semantic
  query cache (default: `true`, backward compatible). Local vLLM
  deployments can disable cache to avoid ineffective writes (T-F-S-1).
- `SAW_SEMANTIC_CACHE_THRESHOLD_MS` env var to skip cache writes when
  embedding API response is below a latency threshold (default: `0`
  = no threshold). `cache.get` still executes for existing entries (T-F-S-1).
- ANN vector index via `hnswlib` (HNSW, MIT, pip-installable) replacing
  full-scan cosine for large-scale semantic search. Auto-switches at
  `SAW_ANN_THRESHOLD` (default 500 [TBD]); falls back to numpy batch
  cosine on failure with `meta.ann_fallback: true` (T-F-S-2, ADR-014).
- `batch_cosine_similarity()` using numpy matrix multiply for small-scale
  / fallback cosine path (constant optimization, no new dependency) (T-F-S-2).
- Benchmark script updated: cache hit measured via `cache.stats().hits`
  counter (not latency comparison); ANN vs cosine P99 comparison;
  100/500/1000/5000 doc scale latency curve (T-F-S-3).
- `related_pages.py` reuses ANN path for embedding similarity (no duplicate
  cosine scan) (T-F-S-2, AC-B-5).

### Changed
- `_semantic_search` cache.get/set now conditional on
  `SAW_SEMANTIC_CACHE_ENABLED` (default unchanged = enabled).
- `_semantic_search` cosine path uses numpy batch matrix multiply instead
  of per-element Python dot product.
- Benchmark `_measure_cache_hit` uses `cache.stats().hits` instead of
  `lat2 < lat1 * 0.5` latency threshold.

### Notes
- `hnswlib` added to `[semantic]` optional dependency (MIT, ~lightweight,
  no faiss/torch).
- No localhost auto-adaptive for cache (explicit env control preferred,
  ADR-014 decision).
- Default behavior unchanged when no `SAW_SEMANTIC_CACHE_*` or
  `SAW_ANN_THRESHOLD` env vars are set.

## [v1.13.0] - 2026-09-06
### Fixed
- `saw ingest <dir>` now recursively ingests all supported files in a
  directory instead of erroring with "Is a directory" (Bug A, T-F-R-1).
- `classifier.py` `is_dir` block returns `UNKNOWN` instead of guessing
  format from children (pipeline handles directories at the entry point).

### Added
- `scripts/benchmark_semantic.py`: real vLLM embedding benchmark
  (semantic vs BM25 recall + P99 latency + cache hit rate, T-F-R-2).
- REST `GET /api/v1/workflows` response items now include `name` and
  `workflow` alias fields (= `definition_name`) for backward compatibility
  (T-F-R-3).

### Changed
- Coverage gate `fail_under` raised from 65 to 67 (T-F-R-4).

### Closed
- Q1 (retrospective-v1.12.0): real API E2E verified — commit `84e1776`
  uses httpx direct to vLLM, semantic search recall confirmed.
- Q3 (retrospective-v1.12.0): ST fallback path removed — provider is
  API-only (httpx direct to vLLM), no ST fallback branch to test.

## [v1.12.0] - 2026-09-05
### Changed
- Embedding provider pivoted from local sentence-transformers to
  OpenAI-style API (litellm.embedding via httpx direct to vLLM). Local
  ST fallback removed (commit `84e1776`). Provider is API-only by default.
### Added
- `EmbeddingSettings` (model/api_key/api_base/timeout) reusing
  LLMSettings env-var pattern.
### Fixed
- Embedding tests no longer `importorskip` sentence-transformers — all
  run via mock litellm.embedding (7 tests moved from skip to pass).

## [v1.11.0] - 2026-09-04
### Changed
- REST `GET /api/v1/workflows` now reads durable `workflow_executions`
  table and merges live in-memory workflows (previously in-memory only).
- Response field renamed from `name` to `definition_name` (aligns with
  DB column). `name` alias added for backward compatibility (see v1.13.0).
### Added
- Semantic search query cache (mode="semantic" key isolation, TTL 300s).
- `compile/compiler.py` deep coverage (20 test cases, 30+ functions).

## [v1.10.0] - 2026-09-03
### Added
- Embedding semantic search (embedding_store table + numpy cosine,
  parallel `--mode semantic` not fused with BM25).
- Smart linking suggest (3-signal + embedding similarity).
