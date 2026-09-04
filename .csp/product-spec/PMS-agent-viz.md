---
type: module-spec
confidence: high
sources:
  - "[[docs/prd/PRD-agent-viz-v1.9.0.md]]"
  - "[[.csp/artifacts/retrospective-v1.8.0.md]]"
seeAlso:
  - "[[code-spec/saw/CODE-MODULE-SPEC.md]] §M11(collaborate)"
created: "2026-09-04"
updated: "2026-09-04"
---

# PMS: agent-viz（agent & workflow 可见性）

> v1.9.0 新能力模块。roadmap v4.3 非 realtime-dashboard 项：workflow durable 历史 list + agent roster CLI + REST。复用 v1.5.0 workflow 基建 + HI-9 表 + build_default_agents。

## 模块边界
- **做什么**：
  - workflow durable 运行历史（`saw workflow list`——DB workflow_executions 表）；
  - agent roster（`saw agents` CLI——6 角色 name/model_tier/tools）；
  - agent roster REST（`GET /api/v1/agents`——前端仪表盘铺路）。
- **不做什么**：realtime WS 仪表盘（大前端工程）；embedding 语义搜索（heavy SDK）；desktop（v4.4）；"最近活动"聚合（需 event bus）。
- **PMS 边界=PRD §2 F-M-1..3**。复用 v1.5.0 既有 workflow_cmd bootstrap + build_default_agents + collaborate router。

## 验收形态
- `saw workflow list` 输出 durable 运行历史表（AC-WF-3）。
- `saw agents` 输出 6 角色表（AC-AG-2）。
- `GET /api/v1/agents` 返回 6 角色 JSON（AC-API-1）。

## 接口契约摘要（ground 自源码）
- workflow_executions 表：`db/migrations.py:_create_workflow_executions`（v4，列 workflow_id/definition_name/status/steps_completed/steps_total/context_json/errors_json/started_at/updated_at/finished_at）。
- workflow CLI bootstrap：`drivers/cli/commands/workflow_cmd.py:_bootstrap_runtime`（v1.5.0，claims.db + apply_migrations）。
- agent roster：`engines/collaborate/agents/__init__.py:build_default_agents(llm_router=None)` → dict[name→BaseAgent]（.name/.model_tier/_tools_allowed/_constraints）。
- collaborate router：`api/routes/collaborate.py:router`（prefix=/api/v1，已有 GET /workflows in-memory）。
- workflow status CLI（v1.5.0 既有单行查）：`workflow_cmd.py:status`。

## 关联
- PRD: `docs/prd/PRD-agent-viz-v1.9.0.md`
- 上游复盘: `.csp/artifacts/retrospective-v1.8.0.md`（L1-L3 deferred）
- 复用 PMS: `PMS-intelligence-adaptation.md`（workflow/agent 域）、`PMS-e2e-usability.md`（CLI）
- 下游 Spec: [待 03 回填] —— F-M-1..3 各 1 Spec
