# ARCHIVE-MANIFEST — v1.18.0

**Milestone**: v1.18.0 (per-request workspace contextvar injection + O4 tag flow)
**Internal Milestone**: v4.8
**Tag**: v1.18.0 (annotated, pending hash backfill)
**Archive Date**: 2026-09-07
**Archiver**: release-manager agent

## A 类 — 一次性发布产物（mv → milestones/v1.18.0/）

> Note: For this release, ship artifacts remain in `.csp/ship/` (living) and are referenced from milestone. The mv happens after release confirmation.

| Path | Type | Source | Git HEAD | Notes |
|---|---|---|---|---|
| ship/RELEASE-NOTES-v1.18.0.md | cp | .csp/ship/RELEASE-NOTES-v1.18.0.md | @pending | Release notes |
| ship/ROLLBACK-PLAN-v1.18.0.md | cp | .csp/ship/ROLLBACK-PLAN-v1.18.0.md | @pending | Rollback plan |

## B 类 — living baseline 快照（cp → milestones/v1.18.0/）

| Path | Type | Source | Git HEAD | Notes |
|---|---|---|---|---|
| specs/SPEC-F-W-1.md | cp | .csp/specs/SPEC-F-W-1.md | @47d5cee | Per-request workspace contextvar spec |
| specs/SPEC-F-W-2.md | cp | .csp/specs/SPEC-F-W-2.md | @47d5cee | O4 tag flow convention spec |
| tasks/TASKS-DELTA-v1.18.0.md | cp | .csp/tasks/TASKS-DELTA-v1.18.0.md | @47d5cee | Task delta for v1.18.0 |
| decomposition/DECOMPOSITION-DELTA-v1.18.0.md | cp | .csp/decomposition/DECOMPOSITION-DELTA-v1.18.0.md | @47d5cee | Decomposition delta |
| tech-decisions/ADR-018-contextvar-per-request-workspace.md | cp | .csp/tech-decisions/ADR/ADR-018-contextvar-per-request-workspace.md | @47d5cee | ADR-018 contextvar decision |
| product-spec/PMS-per-request-ws.md | cp | .csp/product-spec/PMS-per-request-ws.md | @47d5cee | Product spec |
| test-spec/TMS-DELTA-v1.18.0.md | cp | .csp/test-spec/TMS-DELTA-v1.18.0.md | @47d5cee | Test spec delta |
| retrospective-v1.17.0.md | cp | .csp/artifacts/retrospective-v1.17.0.md | @cc9b61a | Previous cycle retrospective (v1.17.0 closure) |

## Verification

| Metric | Value |
|---|---|
| Total files archived | 10 |
| A 类 (ship) | 2 |
| B 类 (baseline snapshots) | 8 |
| pytest | 2277 passed, 7 skipped |
| ruff | 0 errors |
| smoke | 6/6 |
| wheel | smart_agent_wiki-1.18.0-py3-none-any.whl |
