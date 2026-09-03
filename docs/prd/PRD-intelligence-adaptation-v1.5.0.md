---
id: PRD-intelligence-adaptation-v1.5.0
title: 智能与自适应
version: 1.0
status: Released
author: "lifecycle-orchestrator"
date: "2026-09-03"
product_type: platform
feature_count: 4
mvp_scope: [intelligence-adaptation, workflow-orchestration, learn-engine, token-optimization]
thin_sections: [4]
upstream_source: "docs/strategy/ROADMAP.md#v1.5.0 + .csp/artifacts/retrospective-v1.4.0.md (findings H1-H5)"
target_version: v1.5.0
roadmap_ref: ROADMAP
related_pms:
  - .csp/product-spec/PMS-e2e-usability.md
  - .csp/product-spec/PMS-observability.md
related_decomposition: .csp/decomposition/DECOMPOSITION-SUMMARY.md
related_retrospective: .csp/artifacts/retrospective-v1.4.0.md
---

# PRD-intelligence-adaptation-v1.5.0：智能与自适应

> v1.4.0 闭环后的新一轮 01。intelligence-adaptation track：让知识库自我演进——代理编排与学习引擎真实落地。前置依赖 v1.4.0 平台基座（✅）+ 部分债（H1/H2/H4 携带）。

## 1. 背景与动机（roadmap v1.5.0 + 复盘 H1-H5）

v1.4.0 收口平台基座（RBAC/deploy/observability CLI/workspace 隔离 primitive）。复盘（retrospective-v1.4.0.md）回流：
- **H1**：ruff F841（27 死赋值）仍 defer，本轮收口。
- **H2**：workspace 隔离仅 primitive 级，全查询路径路由未做，本轮补。
- **H4**：Cedar 热加载无触发端点，本轮补 `saw policy reload`。
- **H5**：coverage 棘轮 60 未提，本轮补 query 子模块测试提覆盖。
本轮在开智能自适应新能力的同时，携带 H1/H2/H4/H5 债务收口。

## 2. 范围（4 Feature 组）

### F-I-1：多代理 workflow 编排生产级
声明式 workflow yaml + 执行器（复用既有 workflow_executions 表 v4 + HI-9 crash recovery）。
- **AC-WF-1**：`saw workflow run <def.yaml>` 执行多 agent 步骤，crash 可恢复。
- **AC-WF-2**：workflow 定义 schema 校验（失败明确报错）。

### F-I-2：Learn 引擎落地（distill + trends 真实）
v1.3.0 Z-5 让 heavy-SDK 测试优雅 skip；本轮让 Distiller（LLM SOP 提取）+ TrendSenser（gap 检测）真实可用（在线路径），不再仅 rule-fallback。
- **AC-LR-1**：`saw learn distill` 在线产 SOP（非空）。
- **AC-LR-2**：`saw learn gaps` 输出知识缺口列表。

### F-I-3：Token 优化实测
从理论 benchmark 走到实测收益（复用 token_optimizer/session_tracker.py，Z-4 已清 F401）。
- **AC-TK-1**：`saw token bench` 实测 token 节省 % 对比基线。

### F-I-4：agent 角色执行链路一致性校验
6 agent（Writer/Librarian/Critic/Linker/Scholar/Guardian）execute() 真实（v1.2.0 已更正 drift D1）；本轮校验角色调用链一致（哪个 workflow 步骤用哪个 agent，可声明 + 校验）。
- **AC-AG-1**：workflow 步骤声明的 agent 角色与实际调用一致（lint 校验）。

### F-debt-carried（源自 H1/H2/H4/H5）
- **H1**：ruff F841 27 死赋值手修（Z-4b）→ 启用 F841。
- **H2**：workspace 全查询路径路由（QueryEngine/IngestPipeline 注入 workspace scope）。
- **H4**：`saw policy reload` CLI 触发 Cedar 热加载。
- **H5**：补 query 子模块测试，coverage fail_under 上调（60→65+）。

## 3. 非目标
- 多代理 workflow 的可视化编辑器（留 v2.0）。
- 自定义 agent 角色注册（沿用 6 既有）。
- token 优化的模型蒸馏（留 v2.0）。

## 4. 风险
- **F-I-2 Learn 在线**：需 LLM（在线路径），离线仍 fallback；CI 无 LLM，测试须 mock。
- **F-I-1 workflow crash recovery**：workflow_executions 表已存（v4），执行器状态机**已落地**（M-16 WorkflowStatus + _WORKFLOW_TRANSITIONS guard + validate_workflow_transition）；startup recovery 已接（app.py `_recover_stranded_workflows` 标 interrupted）。本轮 gap = CLI surface（`saw workflow run/validate/resume/status`）+ INTERRUPTED→resume 续跑。
- **H2 workspace 全路由**：跨所有 repo 查询注入 workspace_id，面广，须防漏过滤（e2e 守）。

## 5. 下游衔接
- → 02 拆解：F-I-1..4 各拆 Feature + DAG；F-debt-carried 4 债务 task。
- → 03：F-I-1 workflow 状态机需 ADR；F-I-4 agent 角色一致性需 lint 设计。
- → 04：8+ Task；H2 全路由是共享资源串行。
