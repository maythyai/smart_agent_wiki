# Release Notes — v1.18.0

**Release Date**: 2026-09-07
**Internal Milestone**: v4.8
**SemVer Bump**: MINOR (1.17.0 → 1.18.0, additive — no breaking API changes)

## Summary

v1.18.0 delivers **per-request workspace isolation via contextvar injection** — the final piece of the workspace architecture story (closing findings N3/K2 from v1.11.0/v1.7.0). QueryEngine now reads workspace_id from a contextvar per-request, enabling multi-tenant web deployments where each HTTP request operates in its own workspace scope. The public API (QueryEngine constructor signature) is unchanged — this is a fully additive, backward-compatible enhancement. Additionally, the release includes **O4 tag flow convention documentation** ensuring tags always point to release commits (not reconcile commits), improving `git show vX.Y.Z` accuracy.

## What's New

### F-W-1: Per-Request Workspace ContextVar Injection
- **contextvar** `_workspace_id` holds the workspace scope for the current request
- **QueryEngine** internally reads the contextvar (fallback to default workspace) — constructor signature unchanged
- **Web middleware** sets contextvar per-request from URL path (`/ws/{workspace_id}/...`)
- **REST endpoints** (`/workflows`, `/agents`, `/search`, etc.) automatically scope to the current request's workspace
- **Thread-safe & async-safe**: contextvar isolation works across threads and async coroutines
- 7 new tests covering set/get, fallback, isolation, thread-safety, async, middleware, query engine injection

### F-W-2: O4 Tag Flow Convention Documentation
- Documented convention in `release-manager.md` §7.3.5: tag **must** point to the release commit (containing release notes, rollback plan, VERSION-REGISTRY), not the reconcile commit
- `scripts/RELEASE-FLOW.md` standalone flow doc for CI/agent/human reuse
- 3 new tests verifying tag placement convention

## What's Unchanged

- **Public API**: QueryEngine constructor signature, CLI commands, REST endpoints — all unchanged
- **Database schema**: No migrations (contextvar is runtime-only)
- **Dependencies**: No new runtime dependencies added
- **Desktop/Web**: No frontend changes in this release

## Compatibility

- **Backward compatible**: Existing code using QueryEngine with default workspace continues to work identically
- **Python**: Requires ≥3.11 (unchanged from v1.17.0)
- **Upgrade path**: `pip install --upgrade smart-agent-wiki==1.18.0` (no migration needed)

## Quality Gates

| Gate | Result |
|---|---|
| pytest | 2277 passed, 7 skipped, 0 failed |
| ruff | 0 errors |
| smoke | 6/6 passed |
| coverage | ≥67% (fail_under=67) |
| build | smart_agent_wiki-1.18.0-py3-none-any.whl |

## Commits

| Commit | Description |
|---|---|
| 47d5cee | feat(workspace): F-W-1 per-request workspace contextvar + F-W-2 tag flow docs (O4 fix) |
| 88e38f0 | docs(roadmap): v1.18.0 锁定 (per-request workspace + O4 tag, MINOR, v2.0 MAJOR defer) |

## Findings Closed

- **N3/K2**: per-request workspace injection (contested since v1.7.0/v1.11.0) — **resolved** via contextvar
- **O4**: tag pointing to reconcile commit instead of release commit — **resolved** via §7.3.5 convention

## Known Limitations

- Desktop .dmg remains unsigned (ADR-017 defer, same as v1.17.0)
- vLLM benchmark tests skip without local vLLM running (env-dependent, not a regression)
- Coverage 67% floor — gap remains in compile/compiler.py area (deferred to future deep-coverage pass)
