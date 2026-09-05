# Archive Manifest — v1.11.0

**Milestone**: v1.11.0 (债务收口 IV / bug fix)
**Tag**: v1.11.0 @ 5fca85b (local annotated, pending remote push)
**Date**: 2026-09-05
**Internal milestone**: v4.1
**Archived by**: release-manager (06-ship)

## Archived Files

| Path | Type | Source |
|---|---|---|
| specs/SPEC-F-O-1.md | cp | .csp/specs/SPEC-F-O-1.md |
| specs/SPEC-F-O-2.md | cp | .csp/specs/SPEC-F-O-2.md |
| specs/SPEC-F-O-3.md | cp | .csp/specs/SPEC-F-O-3.md |
| specs/SPEC-F-O-4.md | cp | .csp/specs/SPEC-F-O-4.md |
| decomposition/DECOMPOSITION-DELTA-v1.11.0.md | cp | .csp/decomposition/DECOMPOSITION-DELTA-v1.11.0.md |
| decomposition/F-O-1.yaml | cp | .csp/decomposition/FEATURE-DETAILS/F-O-1.yaml |
| decomposition/F-O-2.yaml | cp | .csp/decomposition/FEATURE-DETAILS/F-O-2.yaml |
| decomposition/F-O-3.yaml | cp | .csp/decomposition/FEATURE-DETAILS/F-O-3.yaml |
| decomposition/F-O-4.yaml | cp | .csp/decomposition/FEATURE-DETAILS/F-O-4.yaml |
| tasks/TASKS-DELTA-v1.11.0.md | cp | .csp/tasks/TASKS-DELTA-v1.11.0.md |
| traceability/COVERAGE-REPORT.md | cp | .csp/traceability/COVERAGE-REPORT.md |
| tech-decisions/ADR-011-semantic-search-cache.md | cp | .csp/tech-decisions/ADR/ADR-011-*.md |
| ship/RELEASE-NOTES-v1.11.0.md | cp | .csp/ship/RELEASE-NOTES-v1.11.0.md |
| ship/ROLLBACK-PLAN-v1.11.0.md | cp | .csp/ship/ROLLBACK-PLAN-v1.11.0.md |
| ship/VERSION-REGISTRY.md | cp | .csp/ship/VERSION-REGISTRY.md |
| verify/test-results.md | cp | .csp/artifacts/verify/test-results.md |
| retrospective-v1.10.0.md | cp | .csp/artifacts/retrospective-v1.10.0.md |
| manifest.json | cp | .csp/manifest.json |
| lifecycle-state.json | cp | .csp/lifecycle-state.json (pending update) |

**Note**: All files are B-class cp snapshots (living baseline preserved in .csp/). No A-class mv performed — release not yet pushed to remote, local-only tag. A-class mv (RELEASE-NOTES, ROLLBACK-PLAN, verify report) will be performed after remote push confirms release.

## Quality Gates Summary

| Gate | Result |
|---|---|
| pytest | 2064 passed, 6 skipped, 0 failed |
| ruff | 0 errors |
| coverage | 65.36% (fail_under=65) |
| smoke | 6/6 passed |
| wheel | smart_agent_wiki-1.11.0-py3-none-any.whl (822KB) |
| pyproject version | 1.11.0 |
| multi-platform | desktop 0.1.0 / web 0.1.0 (independent 0.x, OK) |
