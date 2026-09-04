---
id: PRD-agent-viz-v1.9.0
title: Agent & Workflow 可视化（CLI + REST）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-04"
product_type: platform
feature_count: 3
mvp_scope: [workflow-list-durable, agents-roster, agents-rest]
thin_sections: [3]
upstream_source: "docs/strategy/ROADMAP.md#v4.3 + .csp/artifacts/retrospective-v1.8.0.md (findings L1-L3 deferred)"
target_version: v1.9.0
roadmap_ref: ROADMAP
related_pms:
  - .csp/product-spec/PMS-intelligence-adaptation.md
  - .csp/product-spec/PMS-e2e-usability.md
related_decomposition: .csp/decomposition/DECOMPOSITION-SUMMARY.md
related_retrospective: .csp/artifacts/retrospective-v1.8.0.md
---

# PRD-agent-viz-v1.9.0：Agent & Workflow 可视化

> v1.8.0 闭环后的新一轮 01。续新能力，对齐 roadmap v4.3（Agent Visualization）的**非实时仪表盘**项——CLI + REST 可见性，复用 v1.5.0 workflow 基建 + HI-9 持久化表 + 6-agent roster。

## 1. 背景与动机（roadmap v4.3 + 复盘 L1-L3 + embedding 决策）

v1.8.0 转新能力（smart linking）首版成功。本轮续新能力，候选经 review：
- **embedding 语义搜索（v4.2 留尾）defer**：需 sentence-transformers heavy SDK；硬约定 #12"缺依赖须用户确认"——不擅自装；且本环境无法本地验证。本轮不开，留待用户确认装 SDK 后再做。
- **agent 可视化（v4.3）✅ 采纳**：CLI + REST 可见性（非实时 WS 仪表盘——那是更大前端工程），复用既有基建，无重依赖，可本地验证。
- **desktop 完成（v4.4）defer**：Tauri 跨平台构建工程量大，留后续。
- **L1-L3 / K1 / K2** defer：smart-linking 噪声/自动应用、coverage 65、per-request ws——均非本轮。
本轮开 agent + workflow 可见性。

## 2. 范围（3 Feature 组）

### F-M-1：`saw workflow list`（durable 持久化运行历史）
v1.5.0 `saw workflow status <id>` 查单行；本轮补 `list` 列最近 N 条 durable 运行（从 `workflow_executions` 表，HI-9）。**与 REST `GET /api/v1/workflows` 互补**：REST 列 in-memory live 运行（重启丢），CLI 列 DB durable 历史（跨重启）。复用 workflow_cmd bootstrap（claims.db + apply_migrations）。
- **AC-WF-3**：`saw workflow list [--limit 20]` 输出最近运行表（id/name/status/steps/updated），exit 0。

### F-M-2：`saw agents`（6-agent roster）
列出 6 个 agent 角色 + model_tier + tools_allowed + 是否 rule（Guardian 零成本）。复用 `build_default_agents(llm_router=None)`（dispatcher 注册源）。无 DB。
- **AC-AG-2**：`saw agents` 输出 6 角色表（name/model_tier/tools），exit 0。

### F-M-3：`GET /api/v1/agents` REST（roster for frontend）
新端点返回 agent roster（同 F-M-2 数据，JSON），为 v4.3 前端仪表盘铺路。复用 build_default_agents。`GET /api/v1/workflows` 已存在（in-memory），本轮不动。
- **AC-API-1**：`GET /api/v1/agents` 返回 6 角色 JSON（name/model_tier/tools）。

## 3. 非目标
- 实时 WS 仪表盘（v4.3 完整前端工程，留后续）。
- embedding 语义搜索（heavy SDK，须用户确认装，defer）。
- desktop 完成（v4.4，Tauri，defer）。
- L1-L3 / K1 / K2 债务（defer）。

## 4. 风险
- **F-M-1 durable vs live 语义**：CLI list 列 DB 历史，REST /workflows 列 in-memory live——须文档明确互补，避免用户混淆（list 是历史，status 是 live/单行）。
- **F-M-2/F-M-3 roster 静态**：build_default_agents(None) 给静态 roster（无 LLM）；不含"最近活动"（需 event bus 聚合，留后续）。
- **F-M-3 端点鉴权**：复用 auth_dep（authenticated），roster 非敏感只读。

## 5. 下游衔接
- → 02 拆解：F-M-1..3 各拆 Feature + DAG；F-M-2/F-M-3 共享 roster 域。
- → 03：无 ADR（复用基建，无架构变更）；3 Spec 1:1。
- → 04：~3 Task；F-M-1 触 workflow_cmd（v1.5.0 既有文件）；F-M-2/F-M-3 独立。
