# Roadmap: Smart Agent Wiki

## Milestones

- ✅ **v1.1 Collaboration & Visualization** — Phases 1-3 (shipped 2026-04-29) — [Details](milestones/v1.1-ROADMAP.md)
- ✅ **v2.0 Extended Ingestion & Team Platform** — Phases 4-6 (shipped 2026-04-30) — [Details](milestones/v2.0-ROADMAP.md)
- ✅ **v3.0 Ecosystem Integration** — Phases 7-9 (shipped 2026-05-01) — [Details](milestones/v3.0-MILESTONE-AUDIT.md)
- ✅ **v3.1 Third-Party Integrations** — Phases 10-15 (shipped 2026-05-02) — [Details](milestones/v3.1-MILESTONE-AUDIT.md)
- ✅ **v3.2 Platform Enhancements** — Phases 16-20 (shipped 2026-05-03) — [Details](milestones/v3.2-MILESTONE-AUDIT.md)
- 🔵 **v3.3 Tauri Desktop App** — Phases 21-25 (executing) — This document
- ⏳ **v3.4 Code Intelligence** — Phases 26-30 (complete) — [Details](milestones/v3.4-CODE-INTELLIGENCE-PLAN.md)
- ✅ **v3.5 Developer Experience** — Phases 31-34 (shipped 2026-05-05) — This document

## Phases

### Upcoming (v3.3)

- [x] **Phase 21: Tauri Foundation** — Application framework and window management — COMPLETE (2026-05-03)
- [x] **Phase 22: File System Integration** — Drag-drop, file dialogs, folder watching — COMPLETE (2026-05-04)
- [ ] **Phase 23: System Integration** — URL protocol, file association, notifications
- [ ] **Phase 24: Distribution** — Cross-platform builds, auto-update
- [ ] **Phase 25: Backend Sidecar** — Python backend integration

### Phase Details (v3.3)

### Phase 21: Tauri Foundation

**Goal:** 应用框架搭建，实现原生窗口和基础 UI 加载

**Depends on:** v3.2 complete

**Requirements:** APP-01, APP-02, APP-03, APP-04, APP-05, WIN-01, WIN-02, WIN-03, WIN-04, WIN-05

**Success Criteria** (what must be TRUE):
1. User can launch desktop app and see main window
2. App loads existing React UI via WebView
3. Native menu bar works with basic commands
4. System tray icon allows quick access
5. App follows system dark/light theme

**Plans:** 3 plans in 3 waves (COMPLETE)

Plans:
- [x] 21-01-PLAN.md — Tauri project setup and build verification (APP-01~05)
- [x] 21-02-PLAN.md — Window management: menus, tray, close behavior (WIN-01~03)
- [x] 21-03-PLAN.md — Theme detection and keyboard shortcuts (WIN-04~05)

---

### Phase 22: File System Integration

**Goal:** 实现文件系统访问功能

**Depends on:** Phase 21

**Requirements:** FS-01, FS-02, FS-03, FS-04, FS-05

**Success Criteria** (what must be TRUE):
1. User can drag files into app window
2. File dialog opens for file/folder selection
3. Folder watching detects new files
4. Wiki pages can be exported
5. Data stored in standard app directory

**Plans:** 2 plans in 2 waves (COMPLETE)

Plans:
- [x] 22-01-PLAN.md — Drag-drop, file dialogs, app data storage (FS-01, FS-02, FS-05)
- [x] 22-02-PLAN.md — Folder watching and wiki export (FS-03, FS-04)

---

### Phase 23: System Integration

**Goal:** 实现系统集成功能

**Depends on:** Phase 22

**Requirements:** SYS-01, SYS-02, SYS-03, SYS-04, SYS-05

**Success Criteria** (what must be TRUE):
1. saw:// URL protocol opens app
2. App appears in "Open With" for .md/.pdf
3. System notifications work
4. Spotlight/Windows Search finds wiki content
5. Background sync continues when minimized

**Plans:** 0/0 plans

---

### Phase 24: Distribution

**Goal:** 实现跨平台分发和自动更新

**Depends on:** Phase 23

**Requirements:** DIST-01, DIST-02, DIST-03, DIST-04, DIST-05

**Success Criteria** (what must be TRUE):
1. Installers available for all platforms
2. Auto-update downloads and installs new version
3. Version info displayed in app
4. User can skip specific versions
5. Portable mode runs without installation

**Plans:** 0/0 plans

---

### Phase 25: Backend Sidecar

**Goal:** 集成 Python 后端作为 sidecar

**Depends on:** Phase 24

**Requirements:** BACK-01, BACK-02, BACK-03, BACK-04, BACK-05

**Success Criteria** (what must be TRUE):
1. Python backend bundled with app
2. Backend starts automatically with app
3. Backend shuts down gracefully on app close
4. Logs viewable in developer mode
5. Backend parameters configurable

**Plans:** 0/0 plans

---

### Completed (v3.2)

- [x] **Phase 16: Real-Time Dashboard** — WebSocket updates for connector status — Planning (completed 2026-05-03)
- [x] **Phase 17: Mobile Responsive UI** — Layout adaptation for mobile devices — Planning (completed 2026-05-03)
- [x] **Phase 18: Connector Settings** — Per-connector configuration pages — Planning (completed 2026-05-03)
- [x] **Phase 19: Performance Benchmarks** — Rate limiter and sync engine validation — Planning (completed 2026-05-03)
- [x] **Phase 20: Tech Debt Cleanup** — VERIFICATION files, frontend tests, bundle optimization — Planning (completed 2026-05-03)

### Phase Details (v3.2)

### Phase 16: Real-Time Dashboard

**Goal:** Users can see connector status updates in real-time without page refresh

**Depends on:** v3.1 Integration Dashboard

**Requirements:** DASH-01, DASH-02, DASH-03, DASH-04, DASH-05

**Success Criteria** (what must be TRUE):
1. User opens dashboard and sees connector status update automatically
2. System pushes health changes within 1 second of detection
3. Sync progress shows real-time item count and completion percentage
4. WebSocket reconnects gracefully on disconnect with visual indicator
5. User can disable WebSocket updates per connector

**Plans:** 3/3 plans complete

Plans:
- [x] 16-01-PLAN.md — WebSocket server and connection management (DASH-01, DASH-04)
- [x] 16-02-PLAN.md — Real-time status broadcasting and UI integration (DASH-02, DASH-03, DASH-05)

**UI hint:** yes

---

### Phase 17: Mobile Responsive UI

**Goal:** Dashboard renders correctly on mobile devices (320px-768px)

**Depends on:** Phase 16

**Requirements:** MOB-01, MOB-02, MOB-03, MOB-04, MOB-05

**Success Criteria** (what must be TRUE):
1. Dashboard renders correctly on screens as narrow as 320px
2. Integration cards collapse to compact view on mobile
3. Navigation menu collapses to hamburger on small screens
4. Touch gestures (swipe, tap) work correctly
5. Font sizes meet WCAG 2.1 mobile accessibility guidelines

**Plans:** 2/2 plans complete

Plans:
- [x] 17-01-PLAN.md — Responsive layout and navigation (MOB-01, MOB-03, MOB-05)
- [x] 17-02-PLAN.md — Touch interactions and card optimization (MOB-02, MOB-04)

**UI hint:** yes

---

### Phase 18: Connector Settings

**Goal:** Users can configure per-connector settings from dedicated settings pages

**Depends on:** Phase 16

**Requirements:** CONF-01, CONF-02, CONF-03, CONF-04, CONF-05, CONF-06, CONF-07

**Success Criteria** (what must be TRUE):
1. User can access settings page for each connector from dashboard
2. User can change sync interval (5min/15min/1hr/6hr/manual)
3. User can enable/disable sync directions per connector
4. User can view and edit property mappings for Notion/Logseq
5. User can re-authorize expired OAuth tokens from settings
6. Settings persist across server restarts

**Plans:** 2/2 plans complete

Plans:
- [x] 18-01-PLAN.md — Settings API and persistence (CONF-02, CONF-03, CONF-05, CONF-07)
- [x] 18-02-PLAN.md — Settings UI and property mapping editor (CONF-01, CONF-04, CONF-06)

**UI hint:** yes

---

### Phase 19: Performance Benchmarks

**Goal:** System demonstrates rate limiter and sync engine perform correctly under load

**Depends on:** v3.1 Sync Engine

**Requirements:** PERF-01, PERF-02, PERF-03, PERF-04, PERF-05, PERF-06, PERF-07

**Success Criteria** (what must be TRUE):
1. Rate limiter correctly throttles at configured limits under 10x load
2. Token bucket refill behavior matches specification
3. Benchmark report documents latency distribution (p50, p90, p99)
4. Sync engine handles 1000+ items without memory issues
5. Backpressure manager throttles at queue thresholds correctly

**Plans:** 2/2 plans complete

Plans:
- [x] 19-01-PLAN.md — Rate limiter benchmarks (PERF-01, PERF-02, PERF-03, PERF-04)
- [x] 19-02-PLAN.md — Sync engine and backpressure benchmarks (PERF-05, PERF-06, PERF-07)

---

### Phase 20: Tech Debt Cleanup

**Goal:** Resolve accumulated technical debt from v1.1-v3.1

**Depends on:** v3.1 complete

**Requirements:** DEBT-01, DEBT-02, DEBT-03, DEBT-04, DEBT-05, DEBT-06, DEBT-07, DEBT-08

**Success Criteria** (what must be TRUE):
1. All missing Phase VERIFICATION.md files created
2. Vitest configured for React frontend
3. Critical integration components have basic test coverage
4. Bundle analysis report generated
5. Milkdown lazy-loading implemented if needed

**Plans:** 3/3 plans complete

Plans:
- [x] 20-01-PLAN.md — VERIFICATION.md files for Phase 02, 03-01, 03-02, 03-03 (DEBT-01~04)
- [x] 20-02-PLAN.md — Vitest setup and frontend tests (DEBT-05, DEBT-06)
- [x] 20-03-PLAN.md — Bundle analysis and optimization (DEBT-07, DEBT-08)

---

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
| 13. Logseq + IM | v3.1 | 4/4 | Complete | 2026-05-02 |
| 14. GitHub Connector | v3.1 | 3/3 | Complete | 2026-05-02 |
| 15. Dashboard + Polish | v3.1 | 2/2 | Complete | 2026-05-02 |
| 16. Real-Time Dashboard | v3.2 | 3/3 | Complete | 2026-05-03 |
| 17. Mobile Responsive UI | v3.2 | 2/2 | Complete | 2026-05-03 |
| 18. Connector Settings | v3.2 | 2/2 | Complete | 2026-05-03 |
| 19. Performance Benchmarks | v3.2 | 2/2 | Complete | 2026-05-03 |
| 20. Tech Debt Cleanup | v3.2 | 3/3 | Complete | 2026-05-03 |
| 21. Tauri Foundation | v3.3 | 3/3 | Complete | 2026-05-03 |
| 22. File System Integration | v3.3 | 2/2 | Complete | 2026-05-04 |
| 23. System Integration | v3.3 | 0/0 | Not started | - |
| 24. Distribution | v3.3 | 0/0 | Not started | - |
| 25. Backend Sidecar | v3.3 | 0/0 | Not started | - |
| 26. DAG Pipeline Validation | v3.4 | 2/2 | Complete | 2026-05-04 |
| 27. Impact Analysis Engine | v3.4 | 3/3 | Complete | 2026-05-04 |
| 28. Process Detection | v3.4 | 2/2 | Complete | 2026-05-04 |
| 29. Agent Skills Layer | v3.4 | 2/2 | Complete | 2026-05-04 |
| 30. Staleness Detection | v3.4 | 1/1 | Complete | 2026-05-04 |
| 31. Installation | v3.5 | 0/3 | Not started | - |
| 32. Onboarding | v3.5 | 0/3 | Not started | - |
| 33. CLI Usability | v3.5 | 3/3 | Complete | 2026-05-05 |
| 34. Documentation | v3.5 | 2/2 | Complete | 2026-05-05 |

---

## Dependency Graph

```
v3.4 (Complete)
    │
    ▼
Phase 31 (Installation)
    │
    ▼
Phase 32 (Onboarding)
    │
    ▼
Phase 33 (CLI Usability)
    │
    ▼
Phase 34 (Documentation)
    │
    ▼
v3.5: Developer Experience ✓
```

---

*Last updated: 2026-05-05 — v3.5 Developer Experience milestone added*

---

## Upcoming (v3.5: Developer Experience)

- [ ] **Phase 31: Installation** — curl/pipx/Homebrew/Docker 多平台安装支持
- [ ] **Phase 32: Onboarding** — 交互式教程 + 示例目录 + 快速入门文档
- [ ] **Phase 33: CLI Usability** — 短参数 + 友好错误提示 + TUI 配置
- [ ] **Phase 34: Documentation** — 完整文档 + 故障排查 + 迁移指南

### Phase Details (v3.5)

### Phase 31: Installation

**Goal:** 多平台一键安装，自动处理依赖

**Depends on:** v3.4 complete

**Requirements:** INSTALL-01~06

**Success Criteria** (what must be TRUE):
1. curl 一行命令安装成功（Linux/macOS）
2. pipx 安装创建隔离环境
3. Homebrew 安装支持 macOS
4. Docker 镜像零本地依赖
5. 安装脚本自动检测 OS 和依赖
6. `saw --version` 验证安装成功

**Plans:** 0/3 plans

---

### Phase 32: Onboarding

**Goal:** 新用户 5 分钟内完成首次体验

**Depends on:** Phase 31

**Requirements:** ONBOARD-01~05

**Success Criteria** (what must be TRUE):
1. `saw tutorial` 启动交互式引导
2. examples/ 包含 5+ 常见场景示例
3. QUICKSTART.md 可在 5 分钟内完成
4. 在线 Playground 无需安装即可体验
5. 教程自动创建演示 Wiki

**Plans:** 0/3 plans

**UI hint:** yes

---

### Phase 33: CLI Usability

**Goal:** CLI 命令更简洁、友好、易用

**Depends on:** Phase 32

**Requirements:** CLI-01~06

**Success Criteria** (what must be TRUE):
1. 常用命令有短别名（saw i = saw ingest）
2. 错误信息包含修复建议
3. `saw config` 提供 TUI 交互配置
4. 支持 bash/zsh/fish 补全
5. 长操作显示进度条
6. Ctrl+C 优雅取消操作

**Plans:** 3/3 plans (complete)

Plans:
- [x] 33-01-PLAN.md — Short command aliases (CLI-01)
- [x] 33-02-PLAN.md — Friendly error messages and TUI config (CLI-02~03)
- [x] 33-03-PLAN.md — Shell completion and progress indicators (CLI-04~06)

**UI hint:** yes

---

### Phase 34: Documentation

**Goal:** 文档完善，覆盖全场景

**Depends on:** Phase 33

**Requirements:** DOC-01~04

**Success Criteria** (what must be TRUE):
1. `saw help <command>` 显示完整帮助
2. 故障排查指南覆盖常见问题
3. 版本迁移指南完整
4. 离线文档可访问

**Plans:** 2/2 plans (complete)

Plans:
- [x] 34-01-PLAN.md — Command help and troubleshooting guide (DOC-01~02)
- [x] 34-02-PLAN.md — Migration guide and offline docs (DOC-03~04)

---

## Completed (v3.4: Code Intelligence)

### Phase Details (v3.4)

### Phase 26: DAG Pipeline Validation

**Goal:** 为摄入引擎引入 DAG 架构，支持阶段依赖验证和类型安全输出

**Depends on:** v3.3 complete

**Requirements:** DAG-01, DAG-02, DAG-03, DAG-04, DAG-05

**Success Criteria** (what must be TRUE):
1. 每个 pipeline phase 有类型化输出定义
2. 运行时验证阶段依赖完整性（Kahn 拓扑排序）
3. 检测并报告循环依赖（含精确路径）
4. 类型安全访问上游阶段输出
5. 管线配置错误时提供清晰的错误信息

**Plans:** 2/2 plans (planning complete)

Plans:
- [x] 26-01-PLAN.md — DAG types, validator, and runner
- [x] 26-02-PLAN.md — Migrate existing 6 phases to DAG architecture

---

### Phase 27: Impact Analysis Engine

**Goal:** 实现代码修改影响分析，支持上下游依赖追踪和风险分级

**Depends on:** Phase 26

**Requirements:** IMP-01~07

**Success Criteria** (what must be TRUE):
1. 用户可查询任意符号的上下游依赖
2. 结果按深度分层（d=1 WILL BREAK, d=2 LIKELY AFFECTED, d=3 MAY NEED TESTING）
3. 每条依赖边显示置信度分数
4. 支持过滤关系类型（CALLS, IMPORTS, EXTENDS, IMPLEMENTS）
5. 提供 MCP 工具 `saw_impact()`

**Plans:** 0/3 plans

**UI hint:** yes

---

### Phase 28: Process Detection

**Goal:** 自动检测代码执行流程，构建端到端调用链

**Depends on:** Phase 26

**Requirements:** PROC-01~06

**Success Criteria** (what must be TRUE):
1. 系统自动识别入口点（API routes, CLI commands, event handlers）
2. 沿 CALLS 边 BFS 遍历构建执行流程
3. 流程标注类型（intra_community / cross_community）
4. 提供 MCP 工具 `saw_processes()` 和资源

**Plans:** 0/2 plans

**UI hint:** yes

---

### Phase 29: Agent Skills Layer

**Goal:** 创建 Agent Skills 层，引导用户有效使用 MCP 工具

**Depends on:** Phase 27, Phase 28

**Requirements:** SKILL-01~05

**Success Criteria** (what must be TRUE):
1. `.claude/skills/saw/` 目录包含 4 个核心 skill 文件
2. 每个 skill 定义触发条件、工作流步骤、决策树
3. Claude Code 自动检测并加载 skills
4. 用户可通过 `/saw-exploring` 等命令触发 skill

**Plans:** 0/2 plans

---

### Phase 30: Staleness Detection

**Goal:** 实现知识库过期自动检测，与 9 级新鲜度系统联动

**Depends on:** Phase 26

**Requirements:** STALE-01~05

**Success Criteria** (what must be TRUE):
1. 系统比对 last_indexed_commit 与 HEAD
2. 列出变更文件并映射到受影响的 Wiki 页面
3. 生成更新建议
4. 集成到现有 9 级新鲜度系统

**Plans:** 0/1 plan
