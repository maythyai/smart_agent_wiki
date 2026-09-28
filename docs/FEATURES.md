---
id: FEATURES
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-18
status: active
see_also: docs/strategy/ROADMAP.md | docs/strategy/STRATEGY.md
---

# Features — 版本×模块×功能×集成状态矩阵

> 功能列表（roadmap 建规划行，06 标 ✅，07 校准 planned-vs-delivered 漂移）。状态：✅ 已交付 / 📋 规划中 / ⏳ deferred-gate。仅列 v1.19.0+ 本会话 ship + 规划项；既有 v1.0.1–v1.18.1 见 CHANGELOG。

## 已交付（v1.19.0–v1.26.0，竞品借鉴 + 硬化）

| 版本 | 模块 | 功能 | 状态 |
|---|---|---|---|
| v1.19.0 | CLI/links | `saw links rollback`（per-page snapshot restore）| ✅ |
| v1.19.0 | CLI/agents | `saw agents export/import`（portable role YAML，闭合 T3/C4）| ✅ |
| v1.19.0 | CLI/agents | activity 路由 bug 修复（v1.15.0 回归）| ✅ |
| v1.19.0 | collaborate | activity-tracker 解耦（CLI→web 单例移至 collaborate）| ✅ |
| v1.19.0 | query | engine.py 拆分（semantic mixin，881→635）| ✅ |
| v1.20.0 | .claude/skills | C3 saw-tools coding-harness skills 包 | ✅ |
| v1.20.0 | tests | AUDIT-F-04 coverage tests（lint/search/freshness/verify）| ✅ |
| v1.21.0 | govern | B1 contradicts 矛盾边+置信（migration v11 + edges + saw_conflicts 修复）| ✅ |
| v1.22.0 | MCP/agent | C1 saw_resolve + C2 saw_record（task context + durable record）| ✅ |
| v1.23.0 | MCP/agent | A1 saw_wiki_distill（agent 自维护 Wiki）| ✅ |
| v1.23.0 | govern | B2 rethink_contradiction（memory_rethink）| ✅ |
| v1.23.0 | MCP/agent | saw_resolve 语义升级（embeddings→cosine）| ✅ |
| v1.24.0 | query | A2 saw_communities/community_of（Louvain 社区检测）| ✅ |
| v1.24.0 | observability | D1 langfuse_span（env-gated trace export）| ✅ |
| v1.25.0 | query | A3 saw_drift_search（DRIFT global+local hybrid）| ✅ |
| v1.25.0 | domain | B3 ClaimStatus（TRUE/FALSE/SUSPECTED 派生）| ✅ |
| v1.26.0 | ingest | B4 extract_noun_phrases + saw_nlp_keywords（NLP 降本层）| ✅ |
| v1.26.0 | govern | B5 saw_record_feedback（auto-feedback 调置信）| ✅ |
| v1.26.0 | govern | D3 HeartbeatScheduler + saw_heartbeat_status（heartbeat 巡检）| ✅ |

## 规划中（v1.27.0+，下一年路径）

| 版本 | 模块 | 功能 | 状态 |
|---|---|---|---|
| v1.27.0 | write_queue | D2 运维 dashboard（队列深度/背压/失败重试/死信可视化 endpoint）| 📋 |
| v1.27.0 | collaborate | A5 调度自动化（apscheduler 周期 Scholar/Guardian 任务）| 📋 |
| v1.28.0 | plugins | C5a Obsidian 插件（只读 sync + chat 入口）| 📋 |
| v1.28.0 | i18n | i18n 基建（CLI/prompt EN 选项，env-gated）| 📋 |
| v1.29.0 | tests | coverage→70%+（compile/feed/learn/review CLI 功能测试，AUDIT-F-04 续）| 📋 |
| v1.29.0 | perf | 规模性能（ANN ≥500 benchmark / Write Queue 吞吐压测）| 📋 |
| v1.30.0 | research | A4 深度研究模式（Scholar 编排 web+claims→可溯源报告）| 📋 |
| v1.27.0 | write_queue | D2 saw_queue_status（运维 dashboard: per-status/dead-letter/age）| ✅ |
| v1.27.0 | collaborate | A5 AgentScheduler + saw_schedule（apscheduler 周期任务）| ✅ |
| v1.28.0 | plugins | C5a Obsidian 插件（manifest+main.ts: search+sync+settings）| ✅ |
| v1.28.0 | i18n | i18n 基建（tr() helper + SAW_LANG env + 10 EN strings）| ✅ |
| v1.29.0 | tests | thin CLI 功能测试（review/learn/compile/feed，AUDIT-F-04 续）| ✅ |
| v1.30.0 | MCP/agent | A4 saw_deep_research（claims→Writer synthesis report）| ✅ |
| v1.30.0 | api | C5b webhook serving（/api/research + /api/webhook/query）| ✅ |

## 规划中（v1.31.0+，下下年路径 · v2.0 逼近）

> 2026-09-18 外环 roadmap 更新。详见 `docs/strategy/ROADMAP.md` §2.6。状态：📋 规划中。

| 版本 | 模块 | 功能 | 状态 |
|---|---|---|---|
| v1.30.1 | tests | AUDIT-F-02: test_mcp_tools expected_tools 34→35 + README/manifest/test 工具数对齐 | ✅ |
| v1.30.1 | web/nav | AUDIT-F-07: App.tsx 顶部 nav 增 Integrations NavLink | ✅ |
| v1.30.1 | web/a11y | AUDIT-F-09: /integrations 图标按钮补 aria-label | ✅ |
| v1.30.1 | web/ux | AUDIT-F-10: /graph 空状态加 CTA（Import/新建页面） | ✅ |
| v1.30.2 | govern | AUDIT-F-03: WikiIndexer.index_all per-page 容错（坏 YAML 不阻断整库）| ✅ |
| v1.31.0 | govern/MCP | activity 持久化（v12 agent_activity 表 + write-through + load，AUDIT-F-05 闭合）+ GET /api/v1/provenance/{id} REST + saw_verify 增 receipt_id/source_claim_uuid | ✅ |
| v1.31.1 | govern | contamination scan（检测衍生自过期/被取代源的 claim，v1.31.0 deferred 折入）| 📋 |
| v1.32.0 | platform | Compliance & Audit Tier（Ed25519 receipt 导出 + 数据驻留 + 删除传播）| 📋 |
| v1.33.0 | desktop/CI | Playwright E2E + Apple 签名 + 跨平台 CI matrix（AUDIT-F-07/V1/V2）| 📋 |
| v1.34.0 | perf | ANN hnswlib ≥5000 实证 + coverage 72% + Write Queue 压测（S1/S2/O2）| 📋 |
| v1.35.0 | query | Structured Context API v1（统一 vector+graph+ontology+state 路由，★品类定位）| 📋 |
| v1.36.0 | query | claims 图增量更新 + logical-symbolic reasoner（借鉴 LightRAG/KAG 差异化）| 📋 |
| v1.37.0 | ecosystem | Claim Exchange Format v0（联邦互操作种子，借鉴 COGX 差异化）| 📋 |
| v1.38.0 | collaborate | Multi-Agent Orchestration + sleeptime + skill 沉淀（借鉴 Letta/EverOS 差异化）| 📋 |
| v1.39.0 | platform | 4 级 RBAC + per-workspace 配额 + SSO/OIDC + tenant 隔离硬化 | 📋 |
| v1.40.0 | plugins | Plugin Marketplace v1（registry + SDK v1 stable + connector framework）| 📋 |
| v1.41.0 | collaborate | Skill Sandbox 执行（C6 闭合，Docker/E2B）| 📋 |
| v1.42.0 | ecosystem | IM serving 全链路（飞书/Slack/企微）+ Obsidian/Logseq 深集成（C5 续）| 📋 |
| v1.43.0 | code-intel | Coding-Harness 全平台（Codex/Cursor/OpenCode）+ governed code intelligence（vs CodeGraph/Graphify）| 📋 |
| v1.44.0 | token-optimizer | Token ledger 产品化 + cost dashboard + context-compaction（OpenClaw/$47k 痛点）| 📋 |
| v1.45.0 | research | Deep Research v2（多步 web+claims+logical-symbolic→可溯源报告）+ web grounding（A4 续）| 📋 |
| v1.46.0 | collaborate | Agent Self-Evolution + dreaming（批量 reconcile，借鉴 Dreaming V3/EverOS 差异化）| 📋 |
| v1.47.0 | observability | Langfuse-grade trace + W3C traceparent + A2A 适配器（D1 续）| 📋 |
| v1.48.0 | ecosystem | Federated Knowledge Graph v0（跨实例联邦，v3.0 seed）| 📋 |
| v1.49.0 | core-trust | Pre-v2.0 硬化 + `saw migrate v2` + property/fuzz 基建 + coverage 75% | 📋 |
| v1.50.0 | query | v2.0 RC + 统一 Context API freeze + claim exchange v1 stable | 📋 |
| v2.0.0 | platform | 平台化 MAJOR（仅真实 breaking API 变更才 bump）| 📋 |
| v2.1.0 | ecosystem | Marketplace v2 + 多语言 SDK（Python/TS/Rust，内置 provenance 验证）+ 连接器长尾 | 📋 |
| v2.2.0 | ecosystem | 联邦查询生产级 + 跨实例矛盾仲裁 + claim 互操作标准草案 v1 | 📋 |
| v2.3.0 | platform | Governance-as-a-Service（治理 sidecar 嵌入外部 RAG/agent）| 📋 |
| v2.4.0 | query | 多模态编译（image/audio/video/table→claim 锚定原文位置+receipt）| 📋 |
| v2.5.0 | ecosystem | Agent Skill 市场（skill exchange format 携带 provenance）| 📋 |
| v2.6.0 | govern | 自治知识体（Guardian 全自动 expire/置信晋升/矛盾仲裁闭环）| 📋 |
| v2.7.0 | ecosystem | 联邦信任网络（跨实例 trust scoring + receipt notarization 共识）| 📋 |
| v2.8.0 | core-trust | 知识图谱标准提案（claim graph schema 开放标准草案 v1）| 📋 |
| v3.0.0 | ecosystem | 生态/开放 MAJOR（范式跃迁，仅真实 breaking 才 bump）| 📋 |
| v3.1.0 | platform | 行业垂直合规包（医疗 HIPAA/金融/法律 ontology + 审计模板）| 📋 |
| v3.2.0 | ecosystem | 边缘部署（离线自治 + 按需联邦，弱网/断网可用）| 📋 |
| v3.3.0 | ecosystem | 知识资产经济（claim attribution/许可/计费，可信知识可交易）| 📋 |

## deferred-gate（不动，需基建/PRD 决策）

| ID | 模块 | 项 | gate |
|---|---|---|---|
| AUDIT-F-05 | collaborate | agent activity 持久化 | PRD §3.3 rule 6 |
| AUDIT-F-06 | web | banner SPEC 归位（行为正确，risk-gated 重构）| risk |
| AUDIT-F-07 | desktop/CI | desktop 签名 + vLLM CI + Playwright | infra |
| C6 | collaborate | skill sandbox（Docker/E2B）| infra |
