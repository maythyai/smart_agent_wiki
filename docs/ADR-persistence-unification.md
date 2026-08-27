# ADR: Persistence Unification (M-3)

**Status**: Proposed (needs architecture review — do NOT execute blind)
**Date**: 2026-08-27
**Audience**: SAW maintainers

## Context

SAW has **two parallel persistence stacks** that do not share a transaction
boundary or a migration framework:

| Stack | Tables | Driver | Migration | DB file |
|-------|--------|--------|-----------|---------|
| Raw `sqlite3` (claims core) | `claim`, `claim_relation`, `entity`, `entity_relation`, `fts_index`, `write_outbox`, `sink_tracking`, `contradictions`, `workflow_executions` | stdlib `sqlite3` (`check_same_thread=False`) | `saw.db.migrations` (PRAGMA `user_version`, v1–v5) | `.saw/db/claims.db` |
| SQLAlchemy `AsyncSession` (team/connector) | `api_keys`, `users`, `connector_settings`, `sync_state`, `webhooks`, `feeds`, … | `aiosqlite`/`asyncpg` via `saw.db.session` | `Base.metadata.create_all` (no Alembic) | `DATABASE_URL` (default `sqlite:///saw.db`) |

Symptoms already mitigated (not the root cause):
- CR-4 removed the silent `:memory:` fallback on the claims DB.
- Feeds migrated from per-request `:memory:` to a shared persistent engine.
- `create_app_from_config` now sets `busy_timeout`+WAL so the two stacks don't
  hard-fail on each other's locks.

The root cause — **two schemas, two drivers, two migration systems, two files,
no cross-stack transaction** — remains.

## Decision drivers

- A Write-Queue op that enqueues a connector sync (raw sqlite3) **and** updates
  connector settings (SQLAlchemy) cannot be rolled back atomically.
- `join`-able data (claims ↔ connector settings) lives in two files → team
  dashboards that span both are impossible without an in-app merge.
- Two migration frameworks drift independently; `create_all` is non-versioned
  (no downgrades, no auditable change log).

## Options considered

### A. Migrate the claims core to SQLAlchemy AsyncSession (recommended)
- Pros: one driver, one migration framework (add Alembin), one DB, real
  transactions across claims + connectors, async-native (no threadpool
  shims for the claims path).
- Cons: large mechanical change (`SQLiteClaimsRepository`, `SQLiteWriteQueue`,
  `FTS5Search`, `GraphTraverse`, `CodeGraphStore` all become SQLAlchemy); FTS5
  triggers + `saw_tokenize_fts` need re-validation under SQLAlchemy; risk of
  regressing the now-green 1752-test suite.
- **Effort**: 2–3 weeks, behind a feature flag, with a parallel-read period.

### B. Migrate team/connector models to raw sqlite3 + the v6+ migrations
- Pros: keeps the fast sync sqlite3 hot path; one migration framework.
- Cons: loses async (team/asyncpg for PostgreSQL); re-implements ORM by hand;
  biggest risk to the connector surface.
- **Effort**: 2 weeks.

### C. Thin unified repository facade (incremental, low-risk)
- A `UnifiedStore` that owns BOTH connections and exposes a `transaction()`
  context manager doing best-effort two-phase commit (commit claims, then
  connectors; on connector failure, enqueue a compensating op). Does not merge
  schemas but gives a single atomic-ish write boundary + a single health view.
- Pros: small, safe, can ship now; unblocks cross-stack dashboards.
- Cons: does not eliminate the dual schema; a true merge still needed later.
- **Effort**: 3–5 days.

## Recommendation

1. **Now (safe, incremental)** — Option C: a `UnifiedStore` facade + consolidate
   the default DB file so both stacks point at the same SQLite file by default
   (config `DATABASE_URL = sqlite:///{{.saw}}/db/claims.db`), eliminating the
   two-file split for local mode. Add an Alembic skeleton for the SQLAlchemy
   side so its schema becomes versioned.
2. **Next quarter (after review)** — Option A, behind a flag, with a
   parallel-run period and a migration of `FTS5Search`/`CodeGraphStore` first
   (they are the highest-value async wins).

## Why this needs review (not done blind)

- Choosing A vs B determines whether asyncpg/PostgreSQL stays a first-class
  team-deployment target — a product decision, not a refactor mechanic.
- The claims DB has FTS5 virtual tables + a custom `saw_tokenize_fts` SQL
  function registered per-connection; SQLAlchemy's async engine must register
  these via `event.listens_for("connect")` — needs a spike to confirm parity.
- The 1752-test suite is green; a blind migration risks regressing the
  concurrent-dispatch / crash-recovery / CJK-search guarantees just hardened
  (HI-6/7/9, M-17/28).

## Open questions for reviewers

- Is PostgreSQL a required team-deploy target (favors A) or is SQLite-only
  acceptable (favors B)?
- Can the FTS5 + custom tokenizer survive a move to SQLAlchemy's async engine?
- Should the Write Queue stay on raw sqlite3 (it is the hot sync path) even if
  the rest moves to SQLAlchemy?
