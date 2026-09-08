# Release Notes — v1.18.1

> **PATCH** — fix: AUDIT-F-08/W1 sub-service contextvar workspace isolation + W2 E2E test
> Release date: 2026-09-08
> Tag: v1.18.1 (annotated, on release commit)

## Summary

Fixes a **High/P1 cross-workspace data leakage bug** discovered in the v1.18.0 audit. The per-request workspace contextvar injection (v1.18.0, ADR-018) reached `QueryEngine.effective_workspace_id` but not its 3 sub-services — `TreeModeSearch`, `ContextCompiler`, and `GraphTraverse` — which continued reading the instance-level `_workspace_id` set at construction time. In multi-tenant web deployments, this caused the engine's main path to scope workspace A while tree-mode/compiler/graph-traverse pulled workspace B (the default), leading to inconsistent data sources within a single request.

## Changes

### Bug Fix (AUDIT-F-08 / W1)

| File | Change |
|------|--------|
| `src/saw/engines/query/tree_mode.py` | +`effective_workspace_id` property (reads contextvar, falls back to `_workspace_id`); 3 call sites `self._workspace_id` → `self.effective_workspace_id` |
| `src/saw/engines/query/compiler.py` | +`effective_workspace_id` property; 1 call site replaced |
| `src/saw/engines/query/graph_traverse.py` | +`effective_workspace_id` property; +`_loaded_workspace_id` lazy-reload on workspace switch; `_reload_if_stale()` detects contextvar workspace change |

### Test (W2)

| File | Tests |
|------|-------|
| `tests/unit/engines/query/test_subservice_workspace_contextvar.py` | 7 new tests: contextvar set/get/isolation/thread-safety/async/middleware/sub-service consistency |

### Audit Artifacts

- `.csp/audit/AUDIT-VERDICT-v1.18.0-audit.md` — full audit verdict
- `.csp/audit/AUDIT-READINESS-v1.18.0-audit.md` — audit readiness card
- `.csp/audit/AUDIT-FINDINGS-v1.18.0-audit.json` — structured findings
- `.csp/audit/MODULE-LIST-v1.18.0-audit.md` — module decomposition
- `docs/analysis/AUDIT-SUMMARY-v1.18.0-audit.md` — human-readable summary

### Version Bump

- `pyproject.toml`: `1.18.0` → `1.18.1` (PATCH)
- `docs/strategy/ROADMAP.md`: v1.18.1 fix line added; W1/W2 marked fixed

## Security Review (all passed)

| Item | Result | Evidence |
|------|--------|----------|
| .env credentials | ✅ gitignored | `git check-ignore .env` exit=0 |
| SQL injection | ✅ parameterized | All queries use `placeholders` (`?,?,?`) |
| JWT key length | ✅ 256-bit | `secrets.token_hex(32)` (jwt_auth.py:52) |
| write_queue concurrency | ✅ thread-safe | `threading.Lock()` + `check_same_thread=False` |
| Key file permissions | ✅ 0600/0700 | `_keyfiles.py` unified `load_or_create` |

## Verification

```
pytest: 2284 passed, 7 skipped, 0 failed (0 regressions)
  - 7 new sub-service contextvar tests: PASSED
  - 85 query engine tests: PASSED
ruff: All checks passed!
```

## Upgrade

```bash
pip install --upgrade smart-agent-wiki==1.18.1
```

No breaking changes — additive PATCH. Multi-tenant web deployments now correctly scope all query sub-services per-request.
