# Requirements: Smart Agent Wiki

**Defined:** 2026-04-30
**Core Value:** 知识可信、可溯源、可进化 — 每一条回答都可以追溯到原始文档的具体位置

## v2.0 Requirements

Requirements for Extended Ingestion & Team Platform milestone.

### Media Ingestion (Video/Audio)

- [ ] **MING-01**: User can upload video files (MP4, WebM, MOV) for transcription
- [ ] **MING-02**: User can upload audio files (MP3, WAV, M4A, OGG) for transcription
- [ ] **MING-03**: System transcribes video/audio using Whisper (local or API)
- [ ] **MING-04**: System extracts metadata from media files (duration, format, bitrate)
- [ ] **MING-05**: User can configure Whisper model size (tiny/base/small/medium/large)
- [ ] **MING-06**: Transcribed content integrates with existing Claims/Wiki pipeline
- [ ] **MING-07**: System supports batch transcription of multiple media files
- [ ] **MING-08**: User can preview transcription before finalizing ingest

### Team Deployment

- [ ] **TEAM-01**: Administrator can deploy via Docker Compose with single command
- [ ] **TEAM-02**: System supports PostgreSQL as primary database (replacing SQLite)
- [ ] **TEAM-03**: System uses Redis for caching and session management
- [ ] **TEAM-04**: Multiple users can register and authenticate
- [ ] **TEAM-05**: User roles supported (Admin, Editor, Viewer)
- [ ] **TEAM-06**: Knowledge base supports per-user private vaults
- [ ] **TEAM-07**: Shared team vaults with configurable permissions
- [ ] **TEAM-08**: Audit logs track all user actions
- [ ] **TEAM-09**: Data backup and restore functionality
- [ ] **TEAM-10**: Health check endpoints for monitoring

### API Platform

- [ ] **APIP-01**: RESTful API for all CRUD operations on knowledge items
- [ ] **APIP-02**: API key authentication for third-party integrations
- [ ] **APIP-03**: Rate limiting per API key
- [ ] **APIP-04**: OpenAPI/Swagger documentation auto-generated
- [ ] **APIP-05**: Webhook support for ingestion events
- [ ] **APIP-06**: Bulk import/export via API
- [ ] **APIP-07**: GraphQL endpoint for flexible queries
- [ ] **APIP-08**: API versioning support (v1/ prefix)

## v2.1+ Requirements (Deferred)

### Extended Ingestion

- **INGE-10**: Chrome clipper extension for one-click web page capture
- **INGE-11**: RSS feed subscription for automated periodic ingestion
- **INGE-12**: Real-time meeting transcription (Soniox/Whisper)

### Extended Collaboration

- **COLL-06**: Obsidian plugin for bidirectional sync with Obsidian vaults
- **COLL-07**: Tauri desktop application for cross-platform native experience
- **COLL-08**: P2P knowledge sharing between Smart Agent Wiki instances

### Extended Platform

- **PLAT-02**: Multi-language support (English / 中文 / 日本語)
- **PLAT-03**: OWL-RL ontology reasoning for advanced knowledge inference

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time meeting transcription (Soniox) | Requires specific hardware/service, defer to v2.2+ |
| Obsidian plugin | Depends on API Platform, defer to v2.1 |
| Tauri desktop app | Non-core ecosystem expansion, defer to v2.2+ |
| P2P knowledge sharing | Complex networking, defer to v2.3+ |
| Multi-language UI | Internationalization is post-core, defer to v2.2+ |
| OWL-RL reasoning | Advanced feature, defer to v2.2+ |
| Chrome clipper extension | Depends on API Platform, defer to v2.1 |
| RSS subscription | Depends on scheduling infra, defer to v2.1 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MING-01 | Phase 4 | Pending |
| MING-02 | Phase 4 | Pending |
| MING-03 | Phase 4 | Pending |
| MING-04 | Phase 4 | Pending |
| MING-05 | Phase 4 | Pending |
| MING-06 | Phase 4 | Pending |
| MING-07 | Phase 4 | Pending |
| MING-08 | Phase 4 | Pending |
| TEAM-01 | Phase 5 | Pending |
| TEAM-02 | Phase 5 | Pending |
| TEAM-03 | Phase 5 | Pending |
| TEAM-04 | Phase 5 | Pending |
| TEAM-05 | Phase 5 | Pending |
| TEAM-06 | Phase 5 | Pending |
| TEAM-07 | Phase 5 | Pending |
| TEAM-08 | Phase 5 | Pending |
| TEAM-09 | Phase 5 | Pending |
| TEAM-10 | Phase 5 | Pending |
| APIP-01 | Phase 6 | Pending |
| APIP-02 | Phase 6 | Pending |
| APIP-03 | Phase 6 | Pending |
| APIP-04 | Phase 6 | Pending |
| APIP-05 | Phase 6 | Pending |
| APIP-06 | Phase 6 | Pending |
| APIP-07 | Phase 6 | Pending |
| APIP-08 | Phase 6 | Pending |

**Coverage:**
- v2.0 requirements: 26 total
- Mapped to phases: 26
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-30*
*Last updated: 2026-04-30 after v2.0 milestone definition*