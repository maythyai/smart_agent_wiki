# Rollback Plan — v1.18.0

**Version**: v1.18.0
**Release Date**: 2026-09-07
**Previous Stable**: v1.17.0 (@e391611)

## Trigger Conditions

Roll back if ANY of the following within 1 hour of release:
1. **New error types** in production logs related to contextvar/workspace (AttributeError, contextvar leakage across requests)
2. **Workspace isolation breach**: requests seeing data from other workspaces (critical security issue)
3. **QueryEngine regression**: existing single-workspace usage broken (constructor fallback failing)
4. **Performance regression**: P95 latency >50% above v1.17.0 baseline on workspace-scoped queries
5. **Thread-safety issues**: race conditions in contextvar set/get under concurrent load

## Rollback Steps

### Option A: pip downgrade (< 2 min)
```bash
pip install smart-agent-wiki==1.17.0
```
- No DB migration needed (v1.18.0 has no schema changes)
- No config changes needed (contextvar is runtime-only, absent in v1.17.0)
- contextvar simply won't be used; all queries revert to default workspace

### Option B: git revert (< 5 min)
```bash
git revert 47d5cee  # feat(workspace): F-W-1 + F-W-2
git push origin master
```
- Single commit revert — clean, no conflicts expected
- Re-test: `pytest tests/` → should match v1.17.0 baseline (2267 passed)

### Option C: feature flag disable (< 1 min, if web middleware has flag)
- Set `SAW_WORKSPACE_CONTEXTVAR=disabled` env var (if middleware reads it)
- Queries fall back to default workspace without code change

## DB Rollback

**Not needed** — v1.18.0 introduces no database migrations. contextvar is purely runtime state.

## Verification After Rollback

1. `saw smoke` → 6/6 passed
2. `pytest tests/ -q` → 2267 passed, 7 skipped (v1.17.0 baseline)
3. No new error types in logs
4. Existing single-workspace workflows unaffected

## Time Budget

| Action | Estimate |
|---|---|
| pip downgrade | < 2 min |
| git revert + push | < 5 min |
| Smoke verify | < 1 min |
| **Total** | **< 8 min** |

## Communication

- Notify team via Slack/DingTalk: "v1.18.0 rollback initiated — contextvar workspace isolation issue"
- Post-mortem within 24h → findings feed into v1.19.0 backlog
