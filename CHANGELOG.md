# Changelog

All notable changes to this project are documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [v1.20.0] - 2026-09-09
### Added
- **C3 coding-harness skills package** (`.claude/skills/saw-tools/SKILL.md`) —
  teaches coding agents WHEN to call which SAW MCP tool: `saw_impact`/
  `saw_blast_radius` + `saw_code_context` before code changes, `saw_freshness`/
  `saw_status`/`saw_conflicts` for staleness, `saw_verify`/`saw_lint`/`saw_audit`
  after. Closes the deleted phase-29 "agent skills layer" need as a lightweight
  skills package (first competitive-borrow candidate shipped, per
  `docs/analysis/COMPETITIVE-REFERENCE.md`).
- AUDIT-F-04 coverage tests: functional `saw lint` / `saw search` / `saw
  freshness` / `saw verify` (config→repo→governor paths, +4 tests; total
  govern/CLI coverage up).

### Audit
- `.csp/audit/AUDIT-VERDICT-v1.19.0.md` — verdict 放行 (production-ready),
  Critical/High=0, security baseline confirmed (AUDIT-F-08).

### Release Gate
- pytest 2333 passed / 7 skipped / 0 failed; coverage ~67.8% (gate 67); ruff 0;
  vitest 64 pass.

## [v1.19.0] - 2026-09-09
### Added
- `saw links rollback <page>` — restore a page to its pre-`links apply
  --confirm` state from a per-page rollback snapshot saved under
  `.saw/links-rollback/` (T2). `apply --confirm` now snapshots content +
  related before writing.
- `saw agents export <name> --out` / `saw agents import <file>` — portable
  custom-role YAML (validates name/model_tier/system_prompt, rejects
  built-in name collisions, `--force` overwrite). Closes ROADMAP backlog T3.
- CLI smoke tests (`tests/unit/test_cli_smoke.py`) — parametrized `saw <cmd>
  --help` over all 29 commands + root help.
- Functional govern CLI tests (`tests/unit/test_govern_cli.py`) —
  `saw freshness` / `saw verify` config→repo→governor paths.
- Configurable REST polling fallback: `VITE_POLL_INTERVAL_MS` /
  `VITE_STATS_INTERVAL_MS` (shared `web/src/lib/polling.ts`); WS real-time
  path unchanged (U2).
- `docs/analysis/COMPETITIVE-REFERENCE.md` — Phase 0.5 deep-read of 6 peer
  OSS projects (WeKnora/Khoj/GraphRAG/Cognee/Letta/Potpie) with
  differentiated borrow list → ROADMAP v1.20.0+ candidates.

### Fixed
- `saw agents activity <name>` never routed (v1.15.0 regression): the
  `agents` callback (`invoke_without_command=True` + `raise Exit`) intercepted
  every subcommand, so it always printed the roster. Fixed to yield when a
  subcommand is invoked.
- CLI→web coupling: `get_activity_tracker`/`set_activity_tracker` singleton
  moved from `saw.drivers.web.app` to `saw.engines.collaborate.activity_tracker`
  (T4); CLI + REST import from the collaborate module.
- README/README_CN release badge stale (v1.9.0) → aligned to canonical.

### Changed
- S4: `QueryEngine._semantic_search` / `_cosine_search_batch` / `_ann_search`
  extracted to a `SemanticSearchMixin` (`src/saw/engines/query/semantic.py`),
  slimming `engine.py` from 881 → 635 lines. Logic unchanged (mechanical
  move); verified by the semantic/embedding/cache test suite.

### Release gate
- pytest 2329 passed / 7 skipped / 0 failed; coverage 67.76% (gate 67);
  ruff 0; F401 baseline 0; vitest 64 pass.

### Builds on
- v1.18.1 (2026-09-08): fix AUDIT-F-08/W1 sub-service contextvar + W2 E2E.
- v1.18.0 (2026-09-07): per-request workspace contextvar injection + O4 tag flow.

## [v1.17.0] - 2026-09-07
### Added
- Desktop version bumped 0.1.0 → 1.0.0 (desktop/package.json +
  desktop/src-tauri/tauri.conf.json + desktop/src-tauri/Cargo.toml +
  web/package.json). Desktop reaches 1.0 milestone, aligned to canonical
  (T-F-V-1, AC-V-1..4, ADR-017).
- Tauri config convergence: 15-item audit of tauri.conf.json (version,
  frontendDist → `../../web/dist`, devUrl, beforeBuildCommand, bundle
  targets, plugins, IPC commands, release profile) (T-F-V-1).
- Web dashboard integration verified: desktop loads `web/dist` as
  frontendDist, `@tauri-apps/api` ^2.0.0 dependency confirmed,
  dev/prod build chain tested (T-F-V-2).
- Tauri build verification: `tauri build` produces native macOS
  `.app` + `.dmg` bundles (unsigned, per ADR-017 defer) (T-F-V-3).
- Port convergence: vite proxy `8080→8000` for `/api` + `/ws`,
  CORS expanded to `localhost:5173`, prod mode uses external saw
  web server (T-F-V-4, ADR-017).

### Changed
- `web/vite.config.ts` proxy target `8080→8000` (aligns with
  `web_cmd.py` default port 8000).
- `src/saw/web_cmd.py` CORS origins includes `localhost:5173`
  (desktop dev port).
- `src/saw/app.py` CORS fallback list includes `localhost:5173`.
- `pyproject.toml` version `1.16.0 → 1.17.0`.

### Notes
- 50 new pytest tests (version consistency + tauri config +
  web dist/dev integration + bundle targets + port convergence +
  CORS expansion + prod backend + tauri build smoke).
- Tauri build produces unsigned `.dmg` (2.8MB). Code signing
  deferred per ADR-017 (v2.0 candidate).
- Backend changes minimal (4 lines: vite.config.ts 2 +
  web_cmd.py 1 + app.py 1). No backend logic changes.
- No new dependencies. No torch loaded.

## [v1.16.0] - 2026-09-07
### Added
- Realtime dashboard page (`web/src` new route): agent roster table +
  per-agent activity count/recent calls, consuming existing
  `GET /api/v1/agents` + `GET /api/v1/agents/{name}/activity` via
  `@tanstack/react-query` (T-F-U-1, AC-D-1..4, ADR-016).
- Workflow runtime view: recent execution list with status
  (running/done/failed) + step progress, consuming existing
  `GET /api/v1/workflows` (durable + live merge) +
  `GET /api/v1/workflows/{id}/status` (T-F-U-2, AC-D-5..7).
- Realtime update: `react-query` `refetchInterval` polling (15s) +
  existing WebSocket `invalidateQueries` on message. WS disconnect
  triggers polling degraded mode with "Reconnecting..." banner;
  reconnect invalidates cache + 3-failure polling degradation banner
  (T-F-U-3, AC-D-8, ADR-016).

### Changed
- `Dashboard.tsx` migrated from pure WebSocket-driven rendering to
  `react-query` REST data fetching with WS-driven invalidation
  (additive, existing WS path preserved).

### Notes
- Frontend-only release (no backend changes). Consumes v1.15.0 REST
  endpoints (agent roster + activity + workflow status).
- No new dependencies (reuses `@tanstack/react-query` 5.100.6 +
  `zustand` 5.0.12 + `tailwindcss` 4.2.4).
- vitest 64 passed (13 files), 0 failed. tsc + vite build success.
- Backend 2217 passed, 7 skipped (env: vLLM not running + hardcoded
  skips), 0 failed — no regression (frontend-only).

## [v1.15.0] - 2026-09-06
### Added
- Custom agent role registry: users can register custom agent roles
  via YAML configuration (`agents.yaml`), merged with `build_default_agents`
  at runtime. CLI `saw agents --custom` and REST `GET /api/v1/agents`
  list custom + built-in roles (T-F-T-1, ADR-015).
- `saw links apply <page> --suggestion` auto-inserts `[[link]]` into page
  content from `saw links suggest` output. Supports `--dry-run` (preview
  changes) and `--confirm` (interactive confirmation, default on)
  (T-F-T-2).
- Agent activity aggregation: `InMemoryEventBus` subscriber tracks
  `WorkflowStep` events per agent, exposing `GET /api/v1/agents/{name}/activity`
  and CLI `saw agents <name> --activity` returning recent activity and
  call counts (T-F-T-3).

### Changed
- `build_default_agents()` now merges custom roles from `agents.yaml`
  if present (additive, built-in roles always available).
- `links_cmd.py` `suggest` output now includes actionable suggestions
  consumable by `apply` command.

### Notes
- No new dependencies (reuses yaml/typer/fastapi already in project).
- Agent activity counters are in-memory (not persisted) — reset on
  restart by design (ADR-015 candidate ① over ② DB aggregation).
- `examples/demo/sample-documents/utils.py` F841 lint fix (pre-existing
  demo file, removed unused variable assignment).

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
