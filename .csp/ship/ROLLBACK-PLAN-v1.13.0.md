# Rollback Plan — v1.13.0

**Version**: v1.13.0
**Tag**: v1.13.0 (annotated, immutable)
**Commit**: 779d6cb
**Date**: 2026-09-06

## Trigger Conditions

Rollback if any of the following occur post-release:
- Error rate > 2x baseline
- P95 latency > +50% baseline
- User-reported data integrity issues
- Security vulnerability discovered
- Ingestion regression (directory recursion breaks existing single-file ingest)

## Rollback Steps

### Option A: Pin to previous version (preferred, <1min)

1. Pin to v1.12.0 in deployment config: `pip install smart_agent_wiki==1.12.0`
2. Restart service
3. Verify health endpoint reports correct version
4. Notify team

### Option B: Git revert (if code-level rollback needed, <5min)

1. `git revert 779d6cb..0669d98 --no-edit` (revert all v1.13.0 commits)
2. `git push origin master`
3. Tag as `v1.13.1` (patch rollback)
4. Redeploy

### Option C: Feature flag (if available)

N/A — v1.13.0 does not introduce feature flags. All changes are additive/minor.

## Database Rollback

- **No migrations in v1.13.0** — no DB schema changes
- REST alias fields (`name`, `workflow`) are additive response fields, no data migration needed
- Embedding store schema unchanged from v1.12.0

## Verification After Rollback

1. Health endpoint returns 200
2. Version reported == v1.12.0 (or v1.13.1)
3. Smoke tests pass: `saw smoke` 6/6
4. Ingestion of single files works (regression check for F-R-1)
5. REST `/api/v1/workflows` returns correct data (alias fields removed is OK — they were additive)

## Risk Assessment

- **Low risk**: All changes are additive (MINOR). No breaking API changes.
- **F-R-1 (ingest recursion)**: Changes `classifier.py` is_dir handling — if regression, single-file ingest still works (recursion only adds capability, doesn't change existing path).
- **F-R-3 (REST alias)**: Additive response fields — existing consumers unaffected, new consumers get extra fields.
- **F-R-4 (coverage)**: Test-only changes, no production code impact.
- **F-R-2 (benchmark script)**: Standalone script, not imported by any production code.
