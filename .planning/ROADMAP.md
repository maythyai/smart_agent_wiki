# Roadmap: Smart Agent Wiki

## Milestones

- ✅ **v1.1 Collaboration & Visualization** — Phases 1-3 (shipped 2026-04-29) — [Details](milestones/v1.1-ROADMAP.md)
- ✅ **v2.0 Extended Ingestion & Team Platform** — Phases 4-6 (shipped 2026-04-30) — [Details](milestones/v2.0-ROADMAP.md)
- ✅ **v3.0 Ecosystem Integration** — Phases 7-9 (shipped 2026-05-01) — [Details](milestones/v3.0-MILESTONE-AUDIT.md)
- ✅ **v3.1 Third-Party Integrations** — Phases 10-15 (shipped 2026-05-02) — [Details](milestones/v3.1-MILESTONE-AUDIT.md)

## Phases

### Completed (v1.1-v3.0)

- [x] **Phase 7: Obsidian Plugin** — 双向同步与图谱可视化 — COMPLETE
- [x] **Phase 8: Chrome Extension** — 一键剪藏与智能分类 — COMPLETE
- [x] **Phase 9: RSS Subscription** — 自动订阅与增量同步 — COMPLETE

### Completed (v3.1)

- [x] **Phase 10: Connector Framework Foundation** — OAuth infrastructure, unified connector protocol, rate limiting — COMPLETE
- [x] **Phase 11: Sync Engine + Write Queue Integration** — Bidirectional sync, conflict resolution, connector sinks — COMPLETE
- [x] **Phase 12: Notion Connector** — OAuth workspace connection, database sync, property mapping — COMPLETE
- [x] **Phase 13: Logseq + IM Connectors** — Local file sync, Slack/Discord/Feishu/WeCom message ingestion — COMPLETE
- [x] **Phase 14: GitHub Connector** — Issues/Discussions sync, webhook events, repo selection — COMPLETE
- [x] **Phase 15: Integration Dashboard + Polish** — Unified status dashboard, health monitoring, error alerting — COMPLETE

## Phase Details

### Phase 7: Obsidian Plugin — ✅ COMPLETE

**Goal:** 用户可在 Obsidian 中浏览、编辑 SAW 知识库，实现双向同步

**Depends on:** v2.0 API Platform (REST API)

**Requirements:** OBSP-01~07 — All implemented

**Success Criteria:** All 5 criteria met

**Plans:**
- [x] 07-01-PLAN.md — Plugin core implementation
- [x] 07-02-PLAN.md — API client and bidirectional sync logic
- [x] 07-03-PLAN.md — Graph view and confidence badges
- [x] 07-04-PLAN.md — Settings panel and commands

**Delivered:** `plugins/obsidian-smart-agent-wiki/` (24 files, ~2,300 lines)

**UI hint:** yes

---

### Phase 8: Chrome Extension — ✅ COMPLETE

**Goal:** 用户可一键剪藏网页内容到 SAW Vault

**Depends on:** Phase 7, v2.0 API Platform

**Requirements:** CHRE-01~08 — All implemented

**Success Criteria:** All 6 criteria met

**Plans:**
- [x] 08-01-PLAN.md — Extension core (Manifest V3)
- [x] 08-02-PLAN.md — Content extraction (Readability.js)
- [x] 08-03-PLAN.md — Popup UI
- [x] 08-04-PLAN.md — API client and batch operations

**Delivered:** `plugins/chrome-clipper/` (26 files, ~2,750 lines)

**UI hint:** yes

---

### Phase 9: RSS Subscription — ✅ COMPLETE

**Goal:** 用户可订阅 RSS/Atom Feed 并自动摄入新内容

**Depends on:** v2.0 API Platform (ingest endpoint)

**Requirements:** RSSS-01~07 — All implemented

**Success Criteria:** All 6 criteria met

**Plans:**
- [x] 09-01-PLAN.md — Data models and database schema
- [x] 09-02-PLAN.md — FeedManager implementation
- [x] 09-03-PLAN.md — API endpoints
- [x] 09-04-PLAN.md — CLI commands and scheduler

**Delivered:** 7 Python files, ~1,966 lines, 106 tests passing

---

### Phase 10: Connector Framework Foundation

**Goal:** Users can securely connect third-party platforms via OAuth with encrypted credential storage

**Depends on:** v3.0 (shipped)

**Requirements:** AUTH-01, AUTH-02, AUTH-03, AUTH-04, IM-01, IM-02, IM-06

**Success Criteria** (what must be TRUE):
1. User can initiate OAuth flow for Notion/Slack/GitHub/Feishu from Web UI
2. System stores OAuth tokens encrypted at rest using Fernet encryption
3. System automatically refreshes expired tokens with mutex lock
4. Tokens are masked in logs and API responses (showing only last 4 characters)
5. Unified webhook endpoint `/api/v1/webhooks/{platform}` receives and verifies HMAC signatures

**Plans:** 3 plans in 3 waves

Plans:
- [ ] 10-01-PLAN.md — Core connector protocol, models, and registry (AUTH-04, IM-06)
- [ ] 10-02-PLAN.md — OAuth handler and token encryption (AUTH-01, AUTH-02, AUTH-03)
- [ ] 10-03-PLAN.md — Webhook endpoints and rate limiting (IM-01, IM-02, IM-06)

---

### Phase 11: Sync Engine + Write Queue Integration

**Goal:** System can perform bidirectional sync between SAW and connected platforms with conflict detection

**Depends on:** Phase 10

**Requirements:** SYNC-01, SYNC-02, SYNC-03, SYNC-04, SYNC-05, ERRO-01, ERRO-02, ERRO-03, ERRO-04, IM-03, IM-04, IM-05, IM-07

**Success Criteria** (what must be TRUE):
1. User can view sync status dashboard showing all connected platforms
2. System detects sync loops via source metadata tracking
3. All sync operations are logged with timestamp, direction, and item count
4. User can trigger manual sync for any connector from CLI or Web UI
5. System handles backpressure by queuing writes to Write Queue
6. Transient API failures retry with exponential backoff (max 5 retries)
7. Persistent failures trigger alerts and mark connector as unhealthy
8. Per-connector health status is visible in dashboard

**Plans:** 3 plans in 3 waves

Plans:
- [ ] 11-01-PLAN.md — Sync engine core with conflict detection (SYNC-02, SYNC-03, SYNC-05, ERRO-04)
- [ ] 11-02-PLAN.md — Backpressure, retry, and health status (SYNC-01, ERRO-01, ERRO-02, ERRO-03, IM-07)
- [ ] 11-03-PLAN.md — IM message handling and sync API endpoints (SYNC-04, IM-03, IM-04, IM-05)

---

### Phase 12: Notion Connector

**Goal:** Users can sync SAW wiki content bidirectionally with Notion databases

**Depends on:** Phase 10, Phase 11

**Requirements:** NOTI-01, NOTI-02, NOTI-03, NOTI-04, NOTI-05, NOTI-06, NOTI-07, NOTI-08, NOTI-09, NOTI-10

**Success Criteria** (what must be TRUE):
1. User can connect Notion workspace and select databases to sync
2. System ingests new/modified pages from connected databases as Claims
3. Notion properties map correctly to SAW fields (title, content, confidence, freshness)
4. User can edit wiki page in SAW and sync changes back to Notion
5. System detects concurrent edits and resolves by timestamp (last-modified wins)
6. System handles Notion property type changes without crashing
7. System polls for changes at configurable intervals (default: 1 hour)
8. System respects Notion rate limits (3 req/s) with token bucket limiter
9. System resumes sync after interruption using persisted sync cursor

**Plans:** 3 plans in 3 waves

Plans:
- [ ] 12-01-PLAN.md — Notion connector core, OAuth, and database selection (NOTI-01, NOTI-02, NOTI-09, NOTI-10)
- [ ] 12-02-PLAN.md — Property mapping and block transformation (NOTI-03, NOTI-04, NOTI-07)
- [ ] 12-03-PLAN.md — Bidirectional sync, conflict detection, and polling (NOTI-05, NOTI-06, NOTI-08)

---

### Phase 13: Logseq + IM Connectors

**Goal:** Users can sync local Logseq graphs and ingest messages from IM platforms

**Depends on:** Phase 10, Phase 11

**Requirements:** LOGS-01, LOGS-02, LOGS-03, LOGS-04, LOGS-05, LOGS-06, LOGS-07, LOGS-08, LOGS-09, LOGS-10, SLAK-01, SLAK-02, SLAK-03, SLAK-04, SLAK-05, SLAK-06, DISC-01, DISC-02, DISC-03, DISC-04, DISC-05, FEIS-01, FEIS-02, FEIS-03, FEIS-04, FEIS-05, WECO-01, WECO-02, WECO-03, WECO-04

**Success Criteria** (what must be TRUE):

*Logseq:*
1. User can configure local Logseq graph directory path
2. System parses Markdown files and extracts blocks as Claims
3. Property drawers map to Claim metadata correctly
4. System watches directory for file changes in real-time
5. User can edit in SAW and sync changes back to Logseq files
6. System detects concurrent edits and creates conflict copies
7. System preserves Logseq wikilink syntax during sync
8. Logseq namespaces map to SAW Wiki page hierarchy

*IM Platforms:*
9. User can install Slack app and receive message events in real-time
10. User can add Discord bot to server and receive messages via Gateway
11. User can install Feishu app and sync Wiki docs
12. User can configure WeCom bot webhook for message ingestion
13. System captures thread context for threaded messages
14. System handles message reactions as confidence signals
15. System gracefully degrades when platforms are unavailable

**Plans:** 4 plans in 3 waves

Plans:
- [ ] 13-01-PLAN.md — Logseq connector (local file sync, block parsing, file watching) — LOGS-01~10
- [ ] 13-02-PLAN.md — Slack connector (OAuth, Events API, messages) — SLAK-01~06
- [ ] 13-03-PLAN.md — Discord connector (Gateway, reconnection, embeds) — DISC-01~05
- [ ] 13-04-PLAN.md — Feishu + WeCom connectors (webhooks, encryption, Chinese content) — FEIS-01~05, WECO-01~04

---

### Phase 14: GitHub Connector

**Goal:** Users can sync GitHub Issues and Discussions as knowledge sources

**Depends on:** Phase 10, Phase 11

**Requirements:** GITH-01, GITH-02, GITH-03, GITH-04, GITH-05, GITH-06, GITH-07, GITH-08, GITH-09, GITH-10, GITH-11

**Success Criteria** (what must be TRUE):
1. User can connect GitHub account or install GitHub App
2. User can select repositories to sync for Issues/Discussions
3. System ingests Issues as Claims with proper field mapping
4. System ingests Discussions via GraphQL API
5. System receives real-time updates via GitHub webhooks
6. System handles webhook delivery failures with reconciliation job
7. Issue labels map to SAW tags correctly
8. Issue/Discussion comments are captured as related Claims
9. System respects GitHub's 5000 req/hr rate limit
10. System uses conditional requests (ETag/Last-Modified) for efficiency
11. System handles pagination via Link header correctly

**Plans:** 3 plans in 3 waves

Plans:
- [ ] 14-01-PLAN.md — GitHub connector core and OAuth (GITH-01, GITH-02, GITH-09)
- [ ] 14-02-PLAN.md — Issues and Discussions sync (GITH-03, GITH-04, GITH-07, GITH-08)
- [ ] 14-03-PLAN.md — Webhooks and reconciliation (GITH-05, GITH-06, GITH-10, GITH-11)

---

### Phase 15: Integration Dashboard + Polish

**Goal:** Users have unified visibility into all connector health and can manage integrations

**Depends on:** Phase 12, Phase 13, Phase 14

**Requirements:** (Cross-cutting integration, documentation, and final polish)

**Success Criteria** (what must be TRUE):
1. User can view unified dashboard showing all connected platforms
2. Dashboard displays per-connector sync status, last sync time, and health
3. User can disconnect platforms from dashboard
4. User can re-authorize expired OAuth connections
5. System provides clear error messages when sync fails
6. All connector documentation is complete

**Plans:** 2 plans in 2 waves

Plans:
- [ ] 15-01-PLAN.md — Unified dashboard UI and API
- [ ] 15-02-PLAN.md — Documentation and polish

**UI hint:** yes

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Core Data Cycle | v1.1 | 3/3 | Complete | 2026-04-26 |
| 2. Intelligence & Governance | v1.1 | 3/3 | Complete | 2026-04-27 |
| 3-01. Multi-Agent Foundation | v1.1 | 2/2 | Complete | 2026-04-28 |
| 3-02. Web API Foundation | v1.1 | 3/3 | Complete | 2026-04-29 |
| 3-03. React Frontend | v1.1 | 8/8 | Complete | 2026-04-29 |
| 4. Media Ingestion | v2.0 | 3/3 | Complete | 2026-04-30 |
| 5. Team Deployment | v2.0 | 4/4 | Complete | 2026-04-30 |
| 6. API Platform | v2.0 | 3/3 | Complete | 2026-04-30 |
| 7. Obsidian Plugin | v3.0 | 4/4 | Complete | 2026-05-01 |
| 8. Chrome Extension | v3.0 | 4/4 | Complete | 2026-05-01 |
| 9. RSS Subscription | v3.0 | 4/4 | Complete | 2026-05-01 |
| 10. Connector Framework | v3.1 | 3/3 | Complete | 2026-05-02 |
| 11. Sync Engine | v3.1 | 3/3 | Complete | 2026-05-02 |
| 12. Notion Connector | v3.1 | 3/3 | Complete | 2026-05-02 |
| 13. Logseq + IM | v3.1 | 0/4 | Planned | - |
| 14. GitHub Connector | v3.1 | 0/3 | Not started | - |
| 15. Dashboard + Polish | v3.1 | 0/2 | Not started | - |

---

## Dependency Graph

```
v3.0 (Shipped)
    │
    ▼
Phase 10 (Connector Framework)
    │
    ▼
Phase 11 (Sync Engine)
    │
    ├──────────────┬──────────────┐
    ▼              ▼              ▼
Phase 12     Phase 13     Phase 14
(Notion)     (Logseq+IM)  (GitHub)
    │              │              │
    └──────────────┴──────────────┘
                   │
                   ▼
            Phase 15 (Dashboard)
```

---

*Last updated: 2026-05-02 — Phase 13 plans created (4 plans)*