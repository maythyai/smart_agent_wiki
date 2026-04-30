# Requirements: Smart Agent Wiki

**Defined:** 2026-04-30
**Core Value:** 知识可信、可溯源、可进化 — 每一条回答都可以追溯到原始文档的具体位置

## v3.0 Requirements (Ecosystem Integration)

### Obsidian Plugin (OBSP)

**Table Stakes:**

- [ ] **OBSP-01**: 用户可通过 Obsidian 插件浏览 SAW 知识库内容
- [ ] **OBSP-02**: Wiki 页面在 Obsidian 中可编辑并可同步回 SAW
- [ ] **OBSP-03**: 支持 Obsidian 的双向链接 [[]] 语法
- [ ] **OBSP-04**: 插件可通过 SAW API 认证

**Differentiators:**

- [ ] **OBSP-05**: 知识图谱可视化（Cytoscape 风格）
- [ ] **OBSP-06**: 置信度徽章显示在页面标题旁
- [ ] **OBSP-07**: 矛盾检测提示（高亮冲突的 Claims）

### Chrome Extension (CHRE)

**Table Stakes:**

- [ ] **CHRE-01**: 一键剪藏当前页面到 SAW Vault
- [ ] **CHRE-02**: 自动提取正文（去除导航/广告）
- [ ] **CHRE-03**: 支持选择剪藏范围（全文/选中）
- [ ] **CHRE-04**: 添加标签和备注
- [ ] **CHRE-05**: Manifest V3 合规

**Differentiators:**

- [ ] **CHRE-06**: 智能分类建议（基于内容分析）
- [ ] **CHRE-07**: 批量剪藏多个标签页
- [ ] **CHRE-08**: 与 Obsidian 插件协同（剪藏后自动同步）

### RSS Subscription (RSSS)

**Table Stakes:**

- [ ] **RSSS-01**: 订阅 RSS/Atom Feed
- [ ] **RSSS-02**: 自动摄入新文章到 Vault
- [ ] **RSSS-03**: 增量同步（只处理新条目）
- [ ] **RSSS-04**: 配置同步频率

**Differentiators:**

- [ ] **RSSS-05**: 内容变更检测（文章更新时触发重新摄入）
- [ ] **RSSS-06**: Feed 分类管理
- [ ] **RSSS-07**: 按关键词过滤订阅

---

## v2.0 Requirements (Shipped)

All v2.0 requirements have been implemented and verified.

### Media Ingestion (Video/Audio) — ✓ Shipped

- [x] **MING-01**: User can upload video files (MP4, WebM, MOV) for transcription
- [x] **MING-02**: User can upload audio files (MP3, WAV, M4A, OGG) for transcription
- [x] **MING-03**: System transcribes video/audio using Whisper (local or API)
- [x] **MING-04**: System extracts metadata from media files (duration, format, bitrate)
- [x] **MING-05**: User can configure Whisper model size (tiny/base/small/medium/large)
- [x] **MING-06**: Transcribed content integrates with existing Claims/Wiki pipeline
- [x] **MING-07**: System supports batch transcription of multiple media files
- [x] **MING-08**: User can preview transcription before finalizing ingest

### Team Deployment — ✓ Shipped

- [x] **TEAM-01**: Administrator can deploy via Docker Compose with single command
- [x] **TEAM-02**: System supports PostgreSQL as primary database (replacing SQLite)
- [x] **TEAM-03**: System uses Redis for caching and session management
- [x] **TEAM-04**: Multiple users can register and authenticate
- [x] **TEAM-05**: User roles supported (Admin, Editor, Viewer)
- [x] **TEAM-06**: Knowledge base supports per-user private vaults
- [x] **TEAM-07**: Shared team vaults with configurable permissions
- [x] **TEAM-08**: Audit logs track all user actions
- [x] **TEAM-09**: Data backup and restore functionality
- [x] **TEAM-10**: Health check endpoints for monitoring

### API Platform — ✓ Shipped

- [x] **APIP-01**: RESTful API for all CRUD operations on knowledge items
- [x] **APIP-02**: API key authentication for third-party integrations
- [x] **APIP-03**: Rate limiting per API key
- [x] **APIP-04**: OpenAPI/Swagger documentation auto-generated
- [x] **APIP-05**: Webhook support for ingestion events
- [x] **APIP-06**: Bulk import/export via API
- [x] **APIP-07**: GraphQL endpoint for flexible queries
- [x] **APIP-08**: API versioning support (v1/ prefix)

---

## Future Requirements (v3.1+)

| Feature | Target Milestone |
|---------|------------------|
| 第三方集成 (Notion/Logsync) | v3.1+ |
| WebSub 实时推送 | v3.1+ |
| 移动端应用 | v3.3 |
| Tauri 桌面应用 | v3.3 |
| 本体推理 (OWL-RL) | v3.1 |
| 多语言支持 (EN/中文/日语) | v3.1 |

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| P2P 知识共享 | Complex networking, defer to v3.3+ |
| Serverless 部署 | Requires significant architecture changes |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| OBSP-01 | Phase 7 | Pending |
| OBSP-02 | Phase 7 | Pending |
| OBSP-03 | Phase 7 | Pending |
| OBSP-04 | Phase 7 | Pending |
| OBSP-05 | Phase 7 | Pending |
| OBSP-06 | Phase 7 | Pending |
| OBSP-07 | Phase 7 | Pending |
| CHRE-01 | Phase 8 | Pending |
| CHRE-02 | Phase 8 | Pending |
| CHRE-03 | Phase 8 | Pending |
| CHRE-04 | Phase 8 | Pending |
| CHRE-05 | Phase 8 | Pending |
| CHRE-06 | Phase 8 | Pending |
| CHRE-07 | Phase 8 | Pending |
| CHRE-08 | Phase 8 | Pending |
| RSSS-01 | Phase 9 | Pending |
| RSSS-02 | Phase 9 | Pending |
| RSSS-03 | Phase 9 | Pending |
| RSSS-04 | Phase 9 | Pending |
| RSSS-05 | Phase 9 | Pending |
| RSSS-06 | Phase 9 | Pending |
| RSSS-07 | Phase 9 | Pending |

**Coverage:**
- v3.0 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-30*
*Last updated: 2026-04-30 after v3.0 roadmap creation*
