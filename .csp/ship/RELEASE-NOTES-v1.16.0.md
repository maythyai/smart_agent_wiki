# Release v1.16.0 — realtime 仪表盘 v4.3

**Date**: 2026-09-07
**Tag**: v1.16.0
**Type**: additive MINOR (no breaking API changes)
**Commits**: c42df02 (F-U-1) / a95e476 (F-U-2) / 0704e5a (F-U-3)

## Summary

agent/workflow 运行态实时可视化——前端仪表盘展示 agent roster + activity + workflow 执行状态，实时更新。承接 v1.15.0 后端 activity 聚合，前端消费既有 REST 端点，无后端变更。

## What's New

### F-U-1: Agent Roster + Activity Dashboard (ADR-016)

Dashboard page migrated from pure WebSocket-driven rendering to `@tanstack/react-query` REST data fetching. Agent roster table shows all agents (built-in + custom) with per-agent activity count and recent calls.

- **Data sources**: `GET /api/v1/agents` (roster) + `GET /api/v1/agents/{name}/activity` (per-agent activity)
- **Rendering**: `react-query` `useQuery` with cache invalidation
- **AC coverage**: AC-D-1..4

### F-U-2: Workflow Runtime View

New workflow execution list showing recent runs with status (running/done/failed) and step progress. Consumes existing durable + live merge endpoint.

- **Data sources**: `GET /api/v1/workflows` (durable + live merge) + `GET /api/v1/workflows/{id}/status`
- **Components**: `WorkflowList` + `WorkflowRow` (status badge, step progress)
- **AC coverage**: AC-D-5..7

### F-U-3: Realtime Update (Polling + WS Invalidate)

Dual-mode realtime update: `react-query` `refetchInterval` polling (15s) as primary + existing WebSocket `invalidateQueries` on message as instant push. WS disconnect triggers polling degraded mode with "Reconnecting..." banner; reconnect invalidates cache + 3-failure polling degradation banner.

- **Strategy**: react-query refetchInterval 15s (≥10s NFR floor) + WS invalidateQueries (ADR-016 candidate ② > ① SSE > ③ pure WS)
- **Degradation**: WS disconnect → polling-only + banner; polling 3 failures → degradation banner
- **No new backend endpoints**: reuses existing WebSocket + REST
- **AC coverage**: AC-D-8

## Verification

| Gate | Command | Result |
|---|---|---|
| vitest | `cd web && npm test` | 64 passed (13 files), 0 failed |
| frontend build | `cd web && npm run build` | tsc -b + vite build success (1029 modules) |
| pytest | `.venv/bin/python -m pytest tests/ -q` | 2217 passed, 7 skipped, 0 failed |
| ruff | `.venv/bin/ruff check src/ tests/` | 0 errors |
| smoke | `.venv/bin/saw smoke` | 6/6 passed |
| wheel | `.venv/bin/python -m build --wheel` | smart_agent_wiki-1.16.0-py3-none-any.whl (832KB) |
| sdist | `.venv/bin/python -m build --sdist` | smart_agent_wiki-1.16.0.tar.gz (3.2MB) |
| pyproject | version = "1.16.0" | 1.15.0 → 1.16.0 |

### pytest skip details (7 skipped, all environment-dependent)

- 4 benchmark tests: vLLM endpoint unreachable (vLLM not running in this env)
- 3 team_deployment tests: hardcoded `@pytest.mark.skip` (Requires FastAPI/database)

**Note**: v1.16.0 is frontend-only (no backend changes). pytest count differs from v1.15.0 (2220 passed/3 skipped/1 deselected) because vLLM was running during v1.15.0 verify — 3 benchmark tests that passed + 1 deselected are now 4 skipped. 0 failures, 0 errors. No regression.

## Dependencies

No new dependencies. Reuses existing frontend stack:
- `@tanstack/react-query` 5.100.6
- `zustand` 5.0.12
- `tailwindcss` 4.2.4

## Backward Compatibility

- Fully backward compatible — frontend-only release, no backend API changes
- Dashboard.tsx migrated from pure WS to react-query REST + WS invalidate (existing WS path preserved)
- All REST endpoints consumed are from v1.15.0 (already deployed)

## Roadmap

v1.16.0 delivers the realtime dashboard (roadmap v4.3 ecosystem-integration track). Closes M3 (CLI vs REST semantic duality — v1.11.0 already unified REST read DB) by providing frontend visualization of agent/workflow runtime state. Continues findings T1-T4 from retrospective-v1.15.0 (deferred to future iterations).
