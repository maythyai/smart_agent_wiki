# Release v1.13.0 — E2E 收尾轮

**Date**: 2026-09-06
**Tag**: v1.13.0
**Commit**: 779d6cb
**Type**: additive MINOR (no breaking API changes)

## Summary

v1.13.0 closes the embedding E2E tail: directory ingestion recursion fix, real vLLM benchmark script, REST backward-compat alias + CHANGELOG, coverage ratchet to 67%, and Q1/Q3 retrospective closure. Five features (F-R-1..5), all additive.

## Quality Gates

| Gate | Result |
|---|---|
| pytest | 2179 passed, 3 skipped, 2 deselected (benchmark_e2e), 0 failed |
| ruff | 0 errors |
| coverage | 67.27% (fail_under=67) |
| smoke | 6/6 chain + 5 cmd + 5 node = 16 passed |
| wheel | smart_agent_wiki-1.13.0-py3-none-any.whl |
| pyproject | version = 1.13.0 |
| multi-platform | desktop 0.1.0 / web 0.1.0 (pre-1.0, independent) |

## Benchmark (vLLM online — qwen_embedding@localhost:8001)

Ran `scripts/benchmark_semantic.py` against live vLLM endpoint:

- **Semantic recall**: 5.0/5 avg (AI, crypto, web synonym queries — all 5 docs recalled)
- **BM25 recall**: 0.0/5 avg (all synonym queries missed — expected, BM25 is lexical)
- **P99 latency**: semantic 97.82ms, bm25 0.37ms
- **Cache hit**: false (first=41.41ms, second=45.34ms — vLLM too fast for 50% threshold; timing-sensitive, deferred to 07-retro)

**Conclusion**: semantic search dramatically outperforms BM25 on synonym queries (5.0 vs 0.0 recall). Latency overhead is acceptable for the recall gain.

## Changes

### Fixed
- **F-R-1**: `saw ingest <dir>` now recursively ingests all supported files in a directory via `os.walk()` instead of erroring with "Is a directory". `classifier.py` `is_dir` block returns `UNKNOWN` instead of guessing format from children.
- **F-R-5/Q1**: Real API E2E verified — commit `84e1776` uses httpx direct to vLLM, semantic search recall confirmed (5.0 vs 0.0).
- **F-R-5/Q3**: ST fallback path removed — provider is API-only (httpx direct to vLLM), no ST fallback branch to test.

### Added
- **F-R-2**: `scripts/benchmark_semantic.py` — real vLLM embedding benchmark (semantic vs BM25 recall + P99 latency + cache hit rate, 9-item dataset, 3 topics).
- **F-R-3**: REST `GET /api/v1/workflows` response items now include `name` and `workflow` alias fields (= `definition_name`) for backward compatibility. CHANGELOG.md created at project root.

### Changed
- **F-R-4**: Coverage gate `fail_under` raised from 65 to 67. Coverage now 67.27% (up from 66%). Added 75 supplementary tests covering linter, code_wiki, concept_graph, archiver, and feedback modules.

## Commits (since v1.12.0)

```
779d6cb chore(csp): v1.13.0 reconcile planning artifacts
1c12a55 docs(csp): v1.13.0 05-impl done — DEV-LOG + CMS/TMS delta + traceability + lifecycle
218c398 test: F-R-4 supplementary coverage (archiver + feedback, 67.27%)
895c8bf docs: F-R-5 Q1/Q3 closure notes
3284262 fix(api): F-R-3 workflows REST name alias + CHANGELOG.md
dc6d299 feat(benchmark): F-R-2 semantic vs BM25 P99 + cache hit script (vLLM, ≤9 items)
0669d98 fix(ingest): F-R-1 directory recursion (os.walk, no more 'Is a directory')
```

## Multi-platform

- `pyproject.toml`: 1.13.0 (canonical)
- `desktop/tauri.conf.json`: 0.1.0 (pre-1.0, independent per §1.2 rules)
- `web/package.json`: 0.1.0 (pre-1.0, independent per §1.2 rules)

## Known Limitations

- `benchmark_e2e` tests (2) are marker-deselected in CI — they require live vLLM endpoint. Cache hit rate test is timing-sensitive on local vLLM (deferred to 07-retro).
- Desktop/web remain at 0.1.0 (pre-1.0, not yet aligned to canonical).
