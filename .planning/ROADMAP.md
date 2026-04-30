# Roadmap: Smart Agent Wiki

## Milestones

- ✅ **v1.1 Collaboration & Visualization** — Phases 1-3 (shipped 2026-04-29) — [Details](milestones/v1.1-ROADMAP.md)
- 🔄 **v2.0 Extended Ingestion & Team Platform** — Phases 4-6 (active)

## Phases

### v2.0 Milestone (Phases 4-6)

| Phase | Goal | Requirements | Success Criteria |
|-------|------|--------------|-------------------|
| **4. Media Ingestion** | 实现视频/音频转录并集成现有摄入管线 | MING-01~MING-08 | 1. 用户可上传 MP4/MP3 并获得转录文本; 2. 转录内容进入 Claims/Wiki 层; 3. 支持 Whisper 模型配置; 4. 批量转录 10+ 文件正常完成 |
| **5. Team Deployment** | 支持多用户团队协作部署模式 | TEAM-01~TEAM-10 | 1. Docker Compose 一键启动; 2. PostgreSQL 数据库正常工作; 3. 多用户注册/登录成功; 4. 权限系统按角色限制访问; 5. 审计日志可查询 |
| **6. API Platform** | 开放 API 供第三方集成 | APIP-01~APIP-08 | 1. RESTful API 覆盖所有 CRUD; 2. API key 认证工作正常; 3. Swagger 文档自动生成; 4. Webhook 事件推送成功; 5. GraphQL 查询返回正确结果 |

## Phase Details

### Phase 4: Media Ingestion

**Goal:** 实现视频/音频转录并集成现有摄入管线

**Requirements:**
- MING-01: Video file upload (MP4, WebM, MOV)
- MING-02: Audio file upload (MP3, WAV, M4A, OGG)
- MING-03: Whisper transcription (local/API)
- MING-04: Metadata extraction (duration, format, bitrate)
- MING-05: Whisper model configuration
- MING-06: Claims/Wiki pipeline integration
- MING-07: Batch transcription support
- MING-08: Transcription preview before ingest

**Success Criteria:**
1. 用户可上传 MP4/MP3 文件并获得转录文本
2. 转录内容自动进入 Claims/Wiki 存储层
3. 支持 Whisper tiny/base/small/medium/large 模型配置
4. 批量转录 10+ 文件正常完成，无内存溢出
5. 转录预览功能可用，用户可编辑后再确认

**Dependencies:**
- 依赖 v1.1 的摄入引擎架构
- 需要 Whisper 库或 API 接入
- 文件存储扩展（支持大文件）

---

### Phase 5: Team Deployment

**Goal:** 支持多用户团队协作部署模式

**Requirements:**
- TEAM-01: Docker Compose single-command deployment
- TEAM-02: PostgreSQL database support
- TEAM-03: Redis caching and session management
- TEAM-04: Multi-user registration and authentication
- TEAM-05: User roles (Admin, Editor, Viewer)
- TEAM-06: Per-user private vaults
- TEAM-07: Shared team vaults with permissions
- TEAM-08: Audit logs for all actions
- TEAM-09: Backup and restore functionality
- TEAM-10: Health check endpoints

**Success Criteria:**
1. `docker compose up` 一键启动完整系统
2. PostgreSQL 作为主数据库正常工作（替换 SQLite）
3. 至少 3 个用户可同时注册/登录，无冲突
4. Admin 可管理 Editor/Viewer 权限，权限控制生效
5. 审计日志记录所有写入操作，可查询最近 100 条

**Dependencies:**
- 需要 PostgreSQL schema 设计
- 需要 Redis 连接配置
- 需要用户认证系统设计
- 需要权限模型设计（扩展 Cedar）

---

### Phase 6: API Platform

**Goal:** 开放 API 供第三方集成

**Requirements:**
- APIP-01: RESTful API for CRUD operations
- APIP-02: API key authentication
- APIP-03: Rate limiting per API key
- APIP-04: OpenAPI/Swagger auto-documentation
- APIP-05: Webhook support for ingestion events
- APIP-06: Bulk import/export via API
- APIP-07: GraphQL endpoint
- APIP-08: API versioning (v1/ prefix)

**Success Criteria:**
1. RESTful API 覆盖 Vault/Claims/Wiki 所有 CRUD 操作
2. API key 认证拒绝无效请求，接受有效请求
3. Swagger UI 可访问，显示所有端点文档
4. Webhook 在摄入完成后推送事件到配置 URL
5. GraphQL 查询返回正确的嵌套数据结构
6. 速率限制在超限后返回 429 错误

**Dependencies:**
- 依赖 Phase 5 的多用户系统
- 需要 FastAPI REST 框架扩展
- 需要 GraphQL 库（strawberry 或 graphene）
- 需要 Webhook 调度系统

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Core Data Cycle | v1.1 | 3/3 | Complete | 2026-04-26 |
| 2. Intelligence & Governance | v1.1 | 3/3 | Complete | 2026-04-27 |
| 3-01. Multi-Agent Foundation | v1.1 | 2/2 | Complete | 2026-04-28 |
| 3-02. Web API Foundation | v1.1 | 3/3 | Complete | 2026-04-29 |
| 3-03. React Frontend | v1.1 | 8/8 | Complete | 2026-04-29 |
| **4. Media Ingestion** | **v2.0** | **3/3** | **Implemented** | **2026-04-30** |
| **5. Team Deployment** | **v2.0** | **4/4** | **Implemented** | **2026-04-30** |
| **6. API Platform** | **v2.0** | **3/3** | **Complete (Design)** | **2026-04-30** |

---

*Last updated: 2026-04-30 after v2.0 milestone planning*