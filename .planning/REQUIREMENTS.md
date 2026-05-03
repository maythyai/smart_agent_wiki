# Requirements: Smart Agent Wiki

**Defined:** 2026-05-03
**Core Value:** 知识可信、可溯源、可进化 — 每一条回答都可以追溯到原始文档的具体位置

---

## v3.2 Requirements (Platform Enhancements)

### Dashboard Real-Time (DASH)

**WebSocket Updates:**

- [ ] **DASH-01**: User can see real-time connector status updates without page refresh
- [ ] **DASH-02**: System pushes connector health changes via WebSocket within 1 second of detection
- [ ] **DASH-03**: User can see sync progress in real-time (items synced, errors, completion percentage)
- [ ] **DASH-04**: WebSocket connection gracefully reconnects on disconnect with visual indicator
- [ ] **DASH-05**: User can toggle WebSocket updates on/off per connector to control bandwidth

### Mobile Responsive (MOB)

**Layout Adaptation:**

- [ ] **MOB-01**: Dashboard renders correctly on screens 320px-768px wide
- [ ] **MOB-02**: Integration cards collapse to compact view on mobile with expand-on-tap
- [ ] **MOB-03**: Navigation menu collapses to hamburger menu on screens <768px
- [ ] **MOB-04**: Touch gestures work correctly (swipe to dismiss, tap to expand)
- [ ] **MOB-05**: Font sizes and spacing follow mobile accessibility guidelines (WCAG 2.1)

### Connector Settings (CONF)

**Per-Connector Configuration:**

- [ ] **CONF-01**: User can access per-connector settings page from dashboard
- [ ] **CONF-02**: User can configure sync interval per connector (5min/15min/1hr/6hr/manual)
- [ ] **CONF-03**: User can enable/disable specific sync directions (inbound only, outbound only, bidirectional)
- [ ] **CONF-04**: User can view and edit property mappings for Notion/Logseq connectors
- [ ] **CONF-05**: User can configure rate limit overrides per connector (with safety bounds)
- [ ] **CONF-06**: User can re-authorize expired OAuth tokens from settings page
- [ ] **CONF-07**: Settings changes are persisted and survive server restart

### Performance Benchmarks (PERF)

**Rate Limiter Validation:**

- [ ] **PERF-01**: System demonstrates rate limiter correctly throttles at configured limits under 10x load
- [ ] **PERF-02**: System demonstrates token bucket refill behavior matches specification
- [ ] **PERF-03**: Benchmark report documents latency distribution (p50, p90, p99) under various loads
- [ ] **PERF-04**: Benchmark report documents throughput ceiling and bottleneck analysis

**Sync Engine Validation:**

- [ ] **PERF-05**: System demonstrates sync engine handles 1000+ items without memory issues
- [ ] **PERF-06**: Benchmark report documents sync throughput (items/second) per connector
- [ ] **PERF-07**: System demonstrates backpressure manager correctly throttles at queue thresholds

### Tech Debt Cleanup (DEBT)

**Verification Files:**

- [ ] **DEBT-01**: Phase 02 VERIFICATION.md created and committed
- [ ] **DEBT-02**: Phase 03-01 VERIFICATION.md created and committed
- [ ] **DEBT-03**: Phase 03-02 VERIFICATION.md created and committed
- [ ] **DEBT-04**: Phase 03-03 VERIFICATION.md created and committed

**Frontend Tests:**

- [ ] **DEBT-05**: Vitest installed and configured for React frontend
- [ ] **DEBT-06**: Critical integration components have basic test coverage (IntegrationCard, IntegrationList)

**Bundle Optimization:**

- [ ] **DEBT-07**: Bundle analysis report generated and documented
- [ ] **DEBT-08**: Milkdown lazy-loading implemented if bundle exceeds 1MB threshold

---

## v3.1 Requirements (Third-Party Integrations) — ✓ Shipped

### Notion Integration (NOTI)

**Core:**

- [ ] **NOTI-01**: User can connect Notion workspace via OAuth 2.0
- [ ] **NOTI-02**: User can select Notion databases to sync with SAW
- [ ] **NOTI-03**: System automatically ingests new/modified pages from connected databases
- [ ] **NOTI-04**: System maps Notion properties to SAW Claim fields (title, content, confidence, freshness)
- [ ] **NOTI-05**: User can edit pages in SAW and sync changes back to Notion
- [ ] **NOTI-06**: System detects conflicts when both sides modified (timestamp-based resolution)
- [ ] **NOTI-07**: System handles Notion property type changes gracefully
- [ ] **NOTI-08**: System polls for changes at configurable intervals
- [ ] **NOTI-09**: System respects Notion rate limits (3 req/s) with token bucket limiter
- [ ] **NOTI-10**: System persists sync cursor for resume after interruption

### Logseq Integration (LOGS)

**Core:**

- [ ] **LOGS-01**: User can configure Logseq graph path (local directory)
- [ ] **LOGS-02**: System parses Markdown files and extracts blocks as Claims
- [ ] **LOGS-03**: System handles property drawers as Claim metadata
- [ ] **LOGS-04**: System watches Logseq directory for file changes
- [ ] **LOGS-05**: User can edit in SAW and sync changes back to Logseq files
- [ ] **LOGS-06**: System detects concurrent edits (file hash comparison)
- [ ] **LOGS-07**: System creates conflict copies when edits collide
- [ ] **LOGS-08**: System handles EDN format for Logseq configuration
- [ ] **LOGS-09**: System maps Logseq namespaces to SAW Wiki page hierarchy
- [ ] **LOGS-10**: System preserves Logseq wikilink syntax during sync

### IM Integration

**Shared (IM):**

- [ ] **IM-01**: System provides unified webhook endpoint `/api/v1/webhooks/{platform}`
- [ ] **IM-02**: System verifies webhook signatures (HMAC-SHA256)
- [ ] **IM-03**: System extracts message content, author, timestamp, channel
- [ ] **IM-04**: System captures thread context for threaded messages
- [ ] **IM-05**: System handles message reactions as confidence signals
- [ ] **IM-06**: System respects per-platform rate limits
- [ ] **IM-07**: System provides graceful degradation when platforms unavailable

**Slack (SLAK):**

- [ ] **SLAK-01**: User can install Slack app via OAuth 2.0
- [ ] **SLAK-02**: System receives events via Slack Events API
- [ ] **SLAK-03**: System handles message events (message.channels, message.groups)
- [ ] **SLAK-04**: System captures thread replies with parent message context
- [ ] **SLAK-05**: System handles Slack's URL unfurling and attachments
- [ ] **SLAK-06**: System respects Slack's tier-based rate limits

**Discord (DISC):**

- [ ] **DISC-01**: User can add Discord bot to server
- [ ] **DISC-02**: System receives messages via Discord Gateway (WebSocket)
- [ ] **DISC-03**: System handles reconnection with resume sequence
- [ ] **DISC-04**: System captures embeds and attachments
- [ ] **DISC-05**: System respects Discord's 50 req/sec global rate limit

**Feishu (FEIS):**

- [ ] **FEIS-01**: User can install Feishu app via OAuth 2.0
- [ ] **FEIS-02**: System receives messages via Feishu webhook events
- [ ] **FEIS-03**: System handles multi-tenant token (app_token + tenant_token)
- [ ] **FEIS-04**: System captures Feishu Wiki docs as content source
- [ ] **FEIS-05**: System handles Chinese content encoding correctly

**WeCom/企业微信 (WECO):**

- [ ] **WECO-01**: User can configure WeCom bot webhook URL
- [ ] **WECO-02**: System receives messages via WeCom webhook
- [ ] **WECO-03**: System handles WeCom's message encryption (AES-256-CBC)
- [ ] **WECO-04**: System respects WeCom's API rate limits

### GitHub Integration (GITH)

**Core:**

- [ ] **GITH-01**: User can connect GitHub account via OAuth 2.0 or GitHub App
- [ ] **GITH-02**: User can select repositories to sync
- [ ] **GITH-03**: System ingests Issues as Claims with proper field mapping
- [ ] **GITH-04**: System ingests Discussions as Claims (GraphQL API)
- [ ] **GITH-05**: System receives real-time updates via GitHub webhooks
- [ ] **GITH-06**: System handles webhook delivery failures with reconciliation
- [ ] **GITH-07**: System maps Issue labels to SAW tags
- [ ] **GITH-08**: System captures Issue/Discussion comments as related Claims
- [ ] **GITH-09**: System handles GitHub's 5000 req/hr rate limit
- [ ] **GITH-10**: System uses conditional requests (ETag/Last-Modified)
- [ ] **GITH-11**: System handles pagination via Link header correctly

### Cross-Cutting (AUTH, SYNC, ERRO)

**OAuth & Authentication:**

- [ ] **AUTH-01**: System provides unified OAuth flow for all OAuth platforms
- [ ] **AUTH-02**: System stores tokens encrypted at rest
- [ ] **AUTH-03**: System handles token refresh with mutex
- [ ] **AUTH-04**: System masks tokens in logs and API responses

**Sync Engine:**

- [ ] **SYNC-01**: System provides unified sync status dashboard
- [ ] **SYNC-02**: System prevents sync loops (source metadata tracking)
- [ ] **SYNC-03**: System logs all sync operations for audit
- [ ] **SYNC-04**: System provides manual sync trigger per connector
- [ ] **SYNC-05**: System handles backpressure via Write Queue

**Error Handling:**

- [ ] **ERRO-01**: System retries transient failures with exponential backoff
- [ ] **ERRO-02**: System alerts on persistent failures
- [ ] **ERRO-03**: System provides per-connector health status
- [ ] **ERRO-04**: System preserves data integrity on partial failures

---

## v3.0 Requirements (Shipped ✓)

All v3.0 requirements have been implemented and verified.

### Obsidian Plugin (OBSP) — ✓ Shipped

- [x] **OBSP-01**: 用户可通过 Obsidian 插件浏览 SAW 知识库内容
- [x] **OBSP-02**: Wiki 页面在 Obsidian 中可编辑并可同步回 SAW
- [x] **OBSP-03**: 支持 Obsidian 的双向链接 [[]] 语法
- [x] **OBSP-04**: 插件可通过 SAW API 认证
- [x] **OBSP-05**: 知识图谱可视化（Cytoscape 风格）
- [x] **OBSP-06**: 置信度徽章显示在页面标题旁
- [x] **OBSP-07**: 矛盾检测提示（高亮冲突的 Claims）

### Chrome Extension (CHRE) — ✓ Shipped

- [x] **CHRE-01**: 一键剪藏当前页面到 SAW Vault
- [x] **CHRE-02**: 自动提取正文（去除导航/广告）
- [x] **CHRE-03**: 支持选择剪藏范围（全文/选中）
- [x] **CHRE-04**: 添加标签和备注
- [x] **CHRE-05**: Manifest V3 合规
- [x] **CHRE-06**: 智能分类建议（基于内容分析）
- [x] **CHRE-07**: 批量剪藏多个标签页
- [x] **CHRE-08**: 与 Obsidian 插件协同（剪藏后自动同步）

### RSS Subscription (RSSS) — ✓ Shipped

- [x] **RSSS-01**: 订阅 RSS/Atom Feed
- [x] **RSSS-02**: 自动摄入新文章到 Vault
- [x] **RSSS-03**: 增量同步（只处理新条目）
- [x] **RSSS-04**: 配置同步频率
- [x] **RSSS-05**: 内容变更检测（文章更新时触发重新摄入）
- [x] **RSSS-06**: Feed 分类管理
- [x] **RSSS-07**: 按关键词过滤订阅

---

## v2.0 Requirements (Shipped ✓)

All v2.0 requirements have been implemented and verified.

### Media Ingestion (MING) — ✓ Shipped

- [x] **MING-01**: User can upload video files for transcription
- [x] **MING-02**: User can upload audio files for transcription
- [x] **MING-03**: System transcribes video/audio using Whisper
- [x] **MING-04**: System extracts metadata from media files
- [x] **MING-05**: User can configure Whisper model size
- [x] **MING-06**: Transcribed content integrates with Claims/Wiki pipeline
- [x] **MING-07**: System supports batch transcription
- [x] **MING-08**: User can preview transcription before finalizing

### Team Deployment (TEAM) — ✓ Shipped

- [x] **TEAM-01**: Docker Compose deployment
- [x] **TEAM-02**: PostgreSQL support
- [x] **TEAM-03**: Redis for caching and sessions
- [x] **TEAM-04**: Multi-user authentication
- [x] **TEAM-05**: User roles (Admin, Editor, Viewer)
- [x] **TEAM-06**: Per-user private vaults
- [x] **TEAM-07**: Shared team vaults
- [x] **TEAM-08**: Audit logs
- [x] **TEAM-09**: Backup and restore
- [x] **TEAM-10**: Health check endpoints

### API Platform (APIP) — ✓ Shipped

- [x] **APIP-01**: RESTful API for CRUD operations
- [x] **APIP-02**: API key authentication
- [x] **APIP-03**: Rate limiting per API key
- [x] **APIP-04**: OpenAPI documentation
- [x] **APIP-05**: Webhook support
- [x] **APIP-06": Bulk import/export
- [x] **APIP-07**: GraphQL endpoint
- [x] **APIP-08**: API versioning

---

## Out of Scope (v3.2)

| Feature | Reason |
|---------|--------|
| Message sending to IM platforms | Deferred to v3.3+ |
| GitLab integration | Deferred to v3.3+ |
| Advanced analytics dashboard | Deferred to v3.3+ |
| Custom connector SDK | Deferred to v4.0+ |
| Tauri desktop application | v3.3 milestone |
| Multi-language support | v3.3+ milestone |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| DASH-01 | Phase 16 | Pending |
| DASH-02 | Phase 16 | Pending |
| DASH-03 | Phase 16 | Pending |
| DASH-04 | Phase 16 | Pending |
| DASH-05 | Phase 16 | Pending |
| MOB-01 | Phase 17 | Pending |
| MOB-02 | Phase 17 | Pending |
| MOB-03 | Phase 17 | Pending |
| MOB-04 | Phase 17 | Pending |
| MOB-05 | Phase 17 | Pending |
| CONF-01 | Phase 18 | Pending |
| CONF-02 | Phase 18 | Pending |
| CONF-03 | Phase 18 | Pending |
| CONF-04 | Phase 18 | Pending |
| CONF-05 | Phase 18 | Pending |
| CONF-06 | Phase 18 | Pending |
| CONF-07 | Phase 18 | Pending |
| PERF-01 | Phase 19 | Pending |
| PERF-02 | Phase 19 | Pending |
| PERF-03 | Phase 19 | Pending |
| PERF-04 | Phase 19 | Pending |
| PERF-05 | Phase 19 | Pending |
| PERF-06 | Phase 19 | Pending |
| PERF-07 | Phase 19 | Pending |
| DEBT-01 | Phase 20 | Pending |
| DEBT-02 | Phase 20 | Pending |
| DEBT-03 | Phase 20 | Pending |
| DEBT-04 | Phase 20 | Pending |
| DEBT-05 | Phase 20 | Pending |
| DEBT-06 | Phase 20 | Pending |
| DEBT-07 | Phase 20 | Pending |
| DEBT-08 | Phase 20 | Pending |

**Coverage:**
- v3.2 requirements: 32 total
- Mapped to phases: 32/32 (100%)
- Unmapped: 0

---

*Requirements defined: 2026-05-03*
*Last updated: 2026-05-03 — v3.2 requirements defined*