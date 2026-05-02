---
gsd_state_version: 1.0
milestone: v3.1
milestone_name: Third-Party Integrations
status: phase_11_planned
last_updated: "2026-05-02T11:00:00.000Z"
last_activity: 2026-05-02
progress:
  total_phases: 6
  completed_phases: 1
  total_plans: 20
  completed_plans: 3
  percent: 20
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-02)

**Core value:** 知识可信、可溯源、可进化 — 每一条回答都可以追溯到原始文档的具体位置
**Current focus:** v3.1 Third-Party Integrations — Phase 11 planned, ready for execution

## Current Position

Phase: 11 — Sync Engine
Plan: 11-01-PLAN.md (Wave 1)
Status: Phase 11 planned, ready for execution
Last activity: 2026-05-02 — Phase 11 planned (3 plans)

Progress: [███░░░░░░░] 20%

## v3.1 Roadmap Summary

| Phase | Goal | Requirements | Status |
|-------|------|--------------|--------|
| 10 | Connector Framework | AUTH-01~04, IM-01,02,06 (7) | Complete |
| 11 | Sync Engine | SYNC-01~05, ERRO-01~04, IM-03~05,07 (13) | Planned |
| 12 | Notion Connector | NOTI-01~10 (10) | Not started |
| 13 | Logseq + IM | LOGS-01~10, SLAK-01~06, DISC-01~05, FEIS-01~05, WECO-01~04 (30) | Not started |
| 14 | GitHub Connector | GITH-01~11 (11) | Not started |
| 15 | Dashboard + Polish | Cross-cutting (4) | Not started |

**Coverage:** 65/65 requirements mapped (100%)

## Phase 10 Plan Summary

| Plan | Wave | Requirements | Description | Status |
|------|------|--------------|-------------|--------|
| 10-01 | 1 | AUTH-04, IM-06 | Core connector protocol, models, and registry | Complete |
| 10-02 | 2 | AUTH-01, AUTH-02, AUTH-03 | OAuth handler and token encryption | Complete |
| 10-03 | 3 | IM-01, IM-02, IM-06 | Webhook endpoints and rate limiting | Complete |

**Total:** 3 plans, 3 waves, 7 requirements — All complete

## Phase 11 Plan Summary

| Plan | Wave | Requirements | Description | Status |
|------|------|--------------|-------------|--------|
| 11-01 | 1 | SYNC-02, SYNC-03, SYNC-05, ERRO-04 | Sync engine core with conflict detection | Planned |
| 11-02 | 2 | SYNC-01, ERRO-01, ERRO-02, ERRO-03, IM-07 | Backpressure, retry, and health status | Planned |
| 11-03 | 3 | SYNC-04, IM-03, IM-04, IM-05 | IM message handling and sync API endpoints | Planned |

**Total:** 3 plans, 3 waves, 13 requirements — Planned

## Phase 11 Components (New)

### Plan 11-01: Sync Engine Core
- SyncEngine: Bidirectional sync orchestration
- ConflictResolver: Conflict detection and resolution (last_modified_wins)
- SyncStatusTracker: Per-connector sync state tracking
- SyncLogger: Audit logging for all sync operations
- SQLAlchemy models: SyncStateModel, SyncLogModel, ConflictRecordModel

### Plan 11-02: Backpressure, Retry, and Health
- BackpressureManager: Write Queue backpressure handling (pause at 1000, resume at 500)
- RetryHandler: Exponential backoff (1s→2s→4s→8s→16s, max 5 retries)
- HealthMonitor: Three-tier health status (healthy/degraded/unhealthy)
- Health API endpoints: `/api/v1/health`, `/api/v1/health/{connector_id}`

### Plan 11-03: IM Message Handling and Sync API
- MessageHandler: IM message extraction (content, author, timestamp, channel)
- ReactionProcessor: Message reactions to confidence signals
- Sync API endpoints: `/api/v1/sync/status`, `/api/v1/sync/{connector_id}/trigger`
- CLI sync commands: `saw sync status`, `saw sync trigger <connector>`
- ConnectorSink: Write Queue sink for connector operations

## Phase 10 Deliverables

### Plan 10-01: Core Connector Protocol
- UnifiedConnectorInterface Protocol with all required methods
- TokenMasker for AUTH-04 (last 4 chars only)
- RateLimitManager with token bucket for IM-06
- ConnectorRegistry singleton
- SQLAlchemy models: ConnectorConfigModel, ConnectorSyncLog

### Plan 10-02: OAuth Handler and Token Encryption
- TokenEncryption with Fernet for AUTH-02
- OAuthHandler with state management for AUTH-01
- TokenRefreshManager with mutex for AUTH-03
- FastAPI OAuth callback endpoints

### Plan 10-03: Webhook Endpoints and Rate Limiting
- WebhookVerifier with HMAC-SHA256 for IM-02
- WebhookRateLimiter for inbound rate limiting
- WebhookLogger with token masking for audit trail
- Unified webhook endpoint for IM-01

## Previous Milestone Context (v3.0)

**Completed:** 2026-05-01
**Phases:** 3 (07, 08, 09)
**Key deliverables:**
- Obsidian Plugin — 双向同步、图谱可视化
- Chrome Extension — Manifest V3、一键剪藏
- RSS Subscription — fastfeedparser、多键去重

## Accumulated Context

### Decisions (v3.1)

1. **Milestone scope:** 4 platforms (Notion, Logseq, IM, GitHub) all in v3.1
2. **Authentication:** OAuth for Notion/Slack/GitHub, API Token for Logseq
3. **Sync strategy:** SAW as knowledge hub, platforms as sources/consumers
4. **Conflict handling:** Timestamp priority + configurable strategy
5. **Phase numbering:** Continue from Phase 10 (v3.0 ended at Phase 9)
6. **Granularity:** Coarse — 6 phases, aggressive grouping

### Phase 10 Design Decisions

1. **Token encryption:** Fernet with env var `SAW_ENCRYPTION_KEY`
2. **OAuth state:** Redis-based with 10-min TTL for CSRF protection
3. **Rate limiting:** Token bucket per platform (Notion 3/s, GitHub 5000/hr, Slack 60/min, Discord 50/s)
4. **Webhook verification:** Platform-specific HMAC (Slack v0, GitHub sha256=)
5. **Token refresh mutex:** Redis distributed lock (team), asyncio.Lock (single-user)

### Phase 11 Design Decisions (Auto-decided)

1. **Sync loop detection:** Track `source_platform` and `source_id` in Claim metadata
2. **Conflict resolution:** `last_modified_wins` default, store `last_sync_at` per connector
3. **Backpressure:** Pause sync_pull when queue depth > 1000, resume at < 500
4. **Retry:** Exponential backoff 1s→2s→4s→8s→16s (max 5), use `tenacity`
5. **Health status:** `healthy`, `degraded`, `unhealthy` states
6. **Thread context:** Store `thread_parent_id` in Claim metadata
7. **Reactions:** Map to `reactions: {"👍": 5}` in metadata, use as confidence signal

### Architecture Patterns (implemented in Phase 10)

- UnifiedConnectorInterface (Protocol)
- RateLimitManager (per-platform limiting)
- OAuthHandler (unified flow management)
- WebhookVerifier (signature verification)
- WebhookLogger (audit trail)

### New Architecture Patterns (Phase 11)

- SyncEngine (bidirectional orchestration)
- ConflictResolver (timestamp-based resolution)
- BackpressureManager (hysteresis-based throttling)
- RetryHandler (exponential backoff with tenacity)
- HealthMonitor (three-tier status tracking)
- ConnectorSink (Write Queue integration)

### Tech Stack Additions (v3.1)

- notion-client 3.0.0
- slack-sdk 3.41.0 + slack-bolt 1.28.0
- discord.py 2.7.1
- lark-oapi 1.5.5
- PyGithub 2.9.1
- edn-format 0.7.5
- svix 1.92.2
- cryptography 44.0.0
- tenacity (for retry handling)

### Tech Debt (from previous milestones)

1. Integration tests needed for Docker Compose deployment (v2.0)
2. OpenAPI documentation can be auto-generated (v2.0)
3. Performance benchmarks for rate limiter (v2.0)
4. Phase VERIFICATION.md files missing for some phases (v1.1)
5. React frontend tests deferred (v1.1)

### Blockers/Concerns

None — Phase 11 planned, ready for execution.

## Session Continuity

Last session: 2026-05-02T11:00:00.000Z
Next action: `/gsd-execute-phase 11` to execute Phase 11 (Sync Engine)

---
*Last updated: 2026-05-02 — Phase 11 planned*