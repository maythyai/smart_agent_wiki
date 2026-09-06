# Archive Manifest — v1.15.0

**Milestone**: v1.15.0 (agent/link 能力)
**Tag**: v1.15.0 @d5b644f
**Date**: 2026-09-06
**Archived by**: release-manager (06-ship)

## Archived Artifacts

| Path | Type | Source |
|---|---|---|
| `specs/SPEC-F-T-1.md` | cp (B-class) | `.csp/specs/SPEC-F-T-1.md` |
| `specs/SPEC-F-T-2.md` | cp (B-class) | `.csp/specs/SPEC-F-T-2.md` |
| `specs/SPEC-F-T-3.md` | cp (B-class) | `.csp/specs/SPEC-F-T-3.md` |
| `tasks/TASKS-DELTA-v1.15.0.md` | cp (B-class) | `.csp/tasks/TASKS-DELTA-v1.15.0.md` |
| `decomposition/DECOMPOSITION-DELTA-v1.15.0.md` | cp (B-class) | `.csp/decomposition/DECOMPOSITION-DELTA-v1.15.0.md` |
| `tech-decisions/ADR-015-agent-role-registry-activity.md` | cp (B-class) | `.csp/tech-decisions/ADR/ADR-015-agent-role-registry-activity.md` |
| `retrospective-v1.14.0.md` | cp (B-class) | `.csp/artifacts/retrospective-v1.14.0.md` |
| `lifecycle-state.json` | cp (B-class snapshot) | `.csp/lifecycle-state.json` |
| `manifest.json` | cp (B-class snapshot) | `.csp/manifest.json` |

## Git Tag

- **Tag**: v1.15.0 (annotated)
- **Commit**: d5b644f
- **Message**: v1.15.0: agent/link 能力 (F-T-1..3: custom agent role registry + links auto-apply + agent activity aggregation). 2220 passed, ruff 0, coverage 67.42%, smoke 6/6. additive MINOR.
- **Pushed**: origin/master + origin/v1.15.0

## Verification Summary

- pytest: 2220 passed, 3 skipped, 1 deselected
- ruff: 0 errors
- coverage: 67.42% (≥67)
- smoke: 6/6
- wheel: smart_agent_wiki-1.15.0-py3-none-any.whl (832KB)
- sdist: smart_agent_wiki-1.15.0.tar.gz (3.1MB)
- GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.15.0

## Features Delivered

| Feature | Spec | Commit | Description |
|---|---|---|---|
| F-T-1 | SPEC-F-T-1.md | 53cd582 | Custom agent role registry (YAML + CLI + REST) |
| F-T-2 | SPEC-F-T-2.md | 8f6ad2b | Links auto-apply (confirm + dry-run) |
| F-T-3 | SPEC-F-T-3.md | 59f9552 | Agent activity aggregation (event_bus subscriber + REST/CLI) |
