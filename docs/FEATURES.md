---
id: FEATURES
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-15
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
| v1.30.0 | connectors | C5b IM serving（webhook 起步，serve Q&A）| 📋 |

## deferred-gate（不动，需基建/PRD 决策）

| ID | 模块 | 项 | gate |
|---|---|---|---|
| AUDIT-F-05 | collaborate | agent activity 持久化 | PRD §3.3 rule 6 |
| AUDIT-F-06 | web | banner SPEC 归位（行为正确，risk-gated 重构）| risk |
| AUDIT-F-07 | desktop/CI | desktop 签名 + vLLM CI + Playwright | infra |
| C6 | collaborate | skill sandbox（Docker/E2B）| infra |
