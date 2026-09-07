# Archive Manifest — v1.16.0

**Milestone**: v1.16.0 (realtime 仪表盘 v4.3)
**Tag**: v1.16.0 @57b9550
**Date**: 2026-09-07
**Archived by**: release-manager (06-ship)

## Archived Artifacts

| Path | Type | Source |
|---|---|---|
| `specs/SPEC-F-U-1.md` | cp (B-class) | `.csp/specs/SPEC-F-U-1.md` |
| `specs/SPEC-F-U-2.md` | cp (B-class) | `.csp/specs/SPEC-F-U-2.md` |
| `specs/SPEC-F-U-3.md` | cp (B-class) | `.csp/specs/SPEC-F-U-3.md` |
| `tasks/TASKS-DELTA-v1.16.0.md` | cp (B-class) | `.csp/tasks/TASKS-DELTA-v1.16.0.md` |
| `decomposition/DECOMPOSITION-DELTA-v1.16.0.md` | cp (B-class) | `.csp/decomposition/DECOMPOSITION-DELTA-v1.16.0.md` |
| `tech-decisions/ADR-016-realtime-update-strategy.md` | cp (B-class) | `.csp/tech-decisions/ADR/ADR-016-realtime-update-strategy.md` |
| `retrospective-v1.15.0.md` | cp (B-class) | `.csp/artifacts/retrospective-v1.15.0.md` |
| `lifecycle-state.json` | cp (B-class snapshot) | `.csp/lifecycle-state.json` |
| `manifest.json` | cp (B-class snapshot) | `.csp/manifest.json` |

## Git Tag

- **Tag**: v1.16.0 (annotated)
- **Commit**: 57b9550
- **Message**: v1.16.0: realtime 仪表盘 v4.3 (F-U-1..3: agent roster+activity dashboard + workflow runtime view + realtime polling/WS). vitest 64 passed, build OK, backend 2217 passed 7 skipped (env: vLLM not running, no regression frontend-only), ruff 0. additive MINOR.
- **Pushed**: origin/master + origin/v1.16.0

## Verification Summary

| Gate | Result |
|---|---|
| vitest | 64 passed (13 files), 0 failed |
| frontend build | tsc -b + vite build success |
| pytest | 2217 passed, 7 skipped, 0 failed (frontend-only, no backend changes) |
| ruff | 0 errors |
| smoke | 6/6 passed |
| wheel | smart_agent_wiki-1.16.0-py3-none-any.whl (832KB) |
| sdist | smart_agent_wiki-1.16.0.tar.gz (3.2MB) |
| pyproject | version = "1.16.0" (1.15.0 → 1.16.0) |

## GitHub Release

- **URL**: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.16.0
- **Assets**: wheel + sdist
- **Latest**: true

## Features Delivered

- F-U-1: Agent roster + activity dashboard (AC-D-1..4)
- F-U-2: Workflow runtime view (AC-D-5..7)
- F-U-3: Realtime update polling + WS invalidate (AC-D-8)
- AC-D-9: System-level NFR (polling interval ≥10s)

## Notes

- Frontend-only release (no backend changes). Consumes v1.15.0 REST endpoints.
- No new dependencies (reuses @tanstack/react-query 5.100.6 + zustand 5.0.12 + tailwindcss 4.2.4).
- .planning/benchmarks stashed (not committed).
