# Milestones

## v1.1: Collaboration & Visualization

**Shipped:** 2026-04-29
**Phases:** 5 (01, 02, 03-01, 03-02, 03-03)
**Plans:** 19
**Tests:** 430+

### Summary

完整的多代理协作和 Web UI 可视化功能。用户可以通过 6 个专业化 Agent 进行工作流编排，并通过 Web UI 搜索知识库、可视化知识图谱、编辑 Wiki 页面。

### Key Accomplishments

1. **四层存储架构** — 每条主张可溯源到原始文档具体位置
2. **Write Queue Outbox** — 单入口持久化写入，5 个 idempotent sinks
3. **Governance Engine** — 置信度、新鲜度、矛盾检测、审计收据
4. **MCP Server 23 工具** — 所有主流 Agent 兼容
5. **6 Agent 协作架构** — 多模型路由、A2A 协议、Cedar 策略
6. **完整 Web UI** — 搜索、图谱、编辑、Dashboard

### Tech Debt

- Phase VERIFICATION.md files missing (non-blocking)
- React tests deferred (non-blocking)
- Bundle size 1.36MB (acceptable)

### Artifacts

- [Roadmap Archive](milestones/v1.1-ROADMAP.md)
- [Requirements Archive](milestones/v1.1-REQUIREMENTS.md)
- [Audit Report](milestones/v1.1-MILESTONE-AUDIT.md)

---

## v2.0: Extended Ingestion & Team Platform

**Status:** Complete (Design)
**Design Completed:** 2026-04-30
**Phases:** 3 (04, 05, 06)
**Plans:** 10

### Summary

扩展知识摄入渠道（视频/音频）并支持多用户团队协作部署。包含完整的 API 开放平台供第三方集成。

### Key Features Designed

1. **Media Ingestion** — Whisper 转录视频/音频，批量处理，预览确认
2. **Team Deployment** — Docker Compose，PostgreSQL，Redis，多用户认证
3. **API Platform** — RESTful API，API Key，速率限制，GraphQL，Webhook

### Design Documents

- [Media Ingestion Design](../docs/media_ingestion_design.md)
- [Team Deployment Design](../docs/team_deployment_design.md)
- [API Platform Design](../docs/api_platform_design.md)

### Requirements Covered

- MING-01 ~ MING-08 (Media Ingestion)
- TEAM-01 ~ TEAM-10 (Team Deployment)
- APIP-01 ~ APIP-08 (API Platform)

---

*Last updated: 2026-04-30*