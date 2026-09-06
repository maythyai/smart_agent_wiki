# Archive Manifest — v1.14.0

**Milestone**: v1.14.0 (semantic 性能优化)
**Tag**: v1.14.0 (annotated, immutable)
**Commit**: 136befe0503c2db5e08ede38f15527ce9848d557
**Date**: 2026-09-06
**Archived by**: release-manager (S6-ship)

## A-class — One-time ship artifacts (cp snapshot, originals retained in .csp/ship/)

| Path | Type | Source |
|---|---|---|
| ship/RELEASE-NOTES-v1.14.0.md | cp | .csp/ship/RELEASE-NOTES-v1.14.0.md |
| verify/test-results.md | cp | .csp/artifacts/verify/test-results.md |

## B-class — Living baseline snapshots (cp, originals retained in .csp/)

| Path | Type | Source |
|---|---|---|
| specs/SPEC-F-S-1.md | cp | .csp/specs/SPEC-F-S-1.md |
| specs/SPEC-F-S-2.md | cp | .csp/specs/SPEC-F-S-2.md |
| specs/SPEC-F-S-3.md | cp | .csp/specs/SPEC-F-S-3.md |
| decomposition/DECOMPOSITION-DELTA-v1.14.0.md | cp | .csp/decomposition/DECOMPOSITION-DELTA-v1.14.0.md |
| decomposition/F-S-1.yaml | cp | .csp/decomposition/FEATURE-DETAILS/F-S-1.yaml |
| decomposition/F-S-2.yaml | cp | .csp/decomposition/FEATURE-DETAILS/F-S-2.yaml |
| decomposition/F-S-3.yaml | cp | .csp/decomposition/FEATURE-DETAILS/F-S-3.yaml |
| tasks/TASKS-DELTA-v1.14.0.md | cp | .csp/tasks/TASKS-DELTA-v1.14.0.md |
| tech-decisions/ADR-014-ann-vector-index.md | cp | .csp/tech-decisions/ADR/ADR-014-ann-vector-index.md |
| retrospective-v1.13.0.md | cp | .csp/artifacts/retrospective-v1.13.0.md |
| lifecycle-state.json | cp | .csp/lifecycle-state.json |
| manifest.json | cp | .csp/manifest.json |

## Git Anchor

- Tag: `v1.14.0` (annotated, immutable)
- Commit: `136befe`
- GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.14.0

## Quality Summary

- pytest: 2192 passed, 3 skipped, 4 deselected (benchmark_e2e), 0 failed
- ruff: 0 errors
- coverage: 67.34% (fail_under=67)
- smoke: 11/11 passed
- wheel: smart_agent_wiki-1.14.0-py3-none-any.whl (827KB)
- sdist: smart_agent_wiki-1.14.0.tar.gz (3MB)
- hnswlib: MIT license, no torch loaded
- benchmark: semantic recall 5.0/5 vs BM25 0.0/5, P99 54.99ms, cache hit true (R1 resolved), ANN P99 245.23ms vs cosine 72.46ms (15-doc scale)
