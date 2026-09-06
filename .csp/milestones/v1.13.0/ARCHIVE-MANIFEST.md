# Archive Manifest — v1.13.0

**Milestone**: v1.13.0 (E2E 收尾轮)
**Tag**: v1.13.0 (annotated)
**Commit**: 779d6cbfdcda78b62d4f5cedc7308510b70b7556
**Date**: 2026-09-06
**Archived by**: release-manager (S6-ship)

## A-class — One-time ship artifacts (cp snapshot, originals retained in .csp/ship/)

| Path | Type | Source |
|---|---|---|
| ship/RELEASE-NOTES-v1.13.0.md | cp | .csp/ship/RELEASE-NOTES-v1.13.0.md |
| ship/ROLLBACK-PLAN-v1.13.0.md | cp | .csp/ship/ROLLBACK-PLAN-v1.13.0.md |
| ship/VERSION-REGISTRY.md | cp | .csp/ship/VERSION-REGISTRY.md |
| verify/test-results.md | cp | .csp/artifacts/verify/test-results.md |

## B-class — Living baseline snapshots (cp, originals retained in .csp/)

| Path | Type | Source |
|---|---|---|
| specs/SPEC-F-R-1.md | cp | .csp/specs/SPEC-F-R-1.md |
| specs/SPEC-F-R-2.md | cp | .csp/specs/SPEC-F-R-2.md |
| specs/SPEC-F-R-3.md | cp | .csp/specs/SPEC-F-R-3.md |
| specs/SPEC-F-R-4.md | cp | .csp/specs/SPEC-F-R-4.md |
| specs/SPEC-F-R-5.md | cp | .csp/specs/SPEC-F-R-5.md |
| decomposition/DECOMPOSITION-DELTA-v1.13.0.md | cp | .csp/decomposition/DECOMPOSITION-DELTA-v1.13.0.md |
| decomposition/F-R-1.yaml | cp | .csp/decomposition/FEATURE-DETAILS/F-R-1.yaml |
| decomposition/F-R-2.yaml | cp | .csp/decomposition/FEATURE-DETAILS/F-R-2.yaml |
| decomposition/F-R-3.yaml | cp | .csp/decomposition/FEATURE-DETAILS/F-R-3.yaml |
| decomposition/F-R-4.yaml | cp | .csp/decomposition/FEATURE-DETAILS/F-R-4.yaml |
| decomposition/F-R-5.yaml | cp | .csp/decomposition/FEATURE-DETAILS/F-R-5.yaml |
| tasks/TASKS-DELTA-v1.13.0.md | cp | .csp/tasks/TASKS-DELTA-v1.13.0.md |
| tech-decisions/ADR-013-ingest-recursion-benchmark.md | cp | .csp/tech-decisions/ADR/ADR-013-ingest-recursion-benchmark.md |
| retrospective-v1.12.0.md | cp | .csp/artifacts/retrospective-v1.12.0.md |

## Git Anchor

- Tag: `v1.13.0` (annotated, immutable)
- Commit: `779d6cb`
- GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.13.0

## Quality Summary

- pytest: 2179 passed, 3 skipped, 2 deselected (benchmark_e2e), 0 failed
- ruff: 0 errors
- coverage: 67.27% (fail_under=67)
- smoke: 6/6 chain + 5 cmd + 5 node = 16 passed
- wheel: smart_agent_wiki-1.13.0-py3-none-any.whl
- benchmark: semantic recall 5.0 vs BM25 0.0 (vLLM online, qwen_embedding)
