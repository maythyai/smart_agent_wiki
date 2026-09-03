---
type: module-spec
confidence: high
sources:
  - "[[docs/prd/PRD-intelligence-adaptation-v1.5.0.md]]"
  - "[[.csp/code-spec/saw/CODE-MODULE-SPEC.md]]"
  - "[[.csp/artifacts/retrospective-v1.4.0.md]]"
seeAlso:
  - "[[code-spec/saw/CODE-MODULE-SPEC.md]] §M11(collaborate)/§M13(learn)"
created: "2026-09-03"
updated: "2026-09-03"
---

# PMS: intelligence-adaptation（智能与自适应）

> v1.5.0 新增产品模块。把既有"已实现但无 CLI surface / 仅 rule-fallback"的智能能力推到生产可用：多代理 workflow 编排、Learn 引擎在线、Token 优化实测、agent 角色一致性校验。同时携带 v1.4.0 复盘债务 H1/H2/H4/H5。

## 模块边界
- **做什么**：
  - workflow 声明式 YAML 编排的 CLI surface（run/validate/resume/status）+ INTERRUPTED 续跑；
  - Learn 引擎在线 CLI（`saw learn distill` 在线产 SOP / `saw learn gaps` 输出知识缺口）；
  - Token 优化实测 CLI（`saw token bench` 实测节省 % 对比基线）；
  - agent 角色一致性 lint（workflow 步骤声明 agent 与注册角色集一致）。
- **不做什么**：workflow 可视化编辑器（留 v2.0）；自定义 agent 角色注册（沿用 6 既有）；token 模型蒸馏（留 v2.0）；自研新可观测后端（归 observability PMS）。
- **携带债务**：H1 ruff F841 收口（27 死赋值手修 + 启用）；H2 workspace 全查询路径路由（QueryEngine/IngestPipeline 注入 workspace scope）；H4 `saw policy reload` CLI 触发 Cedar 热加载；H5 query 子模块测试 + coverage fail_under 上调 60→65。
- **PMS 边界=PRD §2 F-I-1..4 + F-debt-carried**。

## 验收形态
- `saw workflow run <def.yaml>` 执行多 agent 步骤，crash 后 `saw workflow resume <id>` 可续跑（AC-WF-1）。
- workflow 定义 schema 校验失败明确报错（AC-WF-2）——复用 `WorkflowParser` + `validate(available_agents)`。
- `saw learn distill` 在线产 SOP（非空 payload）；CI 无 LLM 时 mock 不报错（AC-LR-1）。
- `saw learn gaps` 输出 KnowledgeGap 列表（AC-LR-2）。
- `saw token bench` 输出 token 节省 % 对比基线（AC-TK-1）。
- workflow 步骤声明的 agent 角色与 `get_available_agents()` 一致（lint 校验，0 未知角色）（AC-AG-1）。
- `saw policy reload` 触发 Cedar 热加载（返回 reload 结果）。
- ruff F841 启用后 src/ 0 errors；coverage fail_under=65 且 CI 绿。

## 接口契约摘要（ground 自源码，行号以源码为准）
- workflow 执行：`engines/collaborate/workflow_executor.py:WorkflowExecutor.execute_definition`（state machine M-16 + HI-9 `_persist_workflow`）。
- workflow 解析/校验：`engines/collaborate/workflow_parser.py:WorkflowParser.parse` + `validate(workflow, available_agents)`。
- startup recovery：`drivers/web/app.py:_recover_stranded_workflows`（标 running→interrupted）。
- Learn distill：`engines/learn/distiller.py:Distiller.extract_sop`（LLMRouter.extract_claims 在线路径）+ `run_distillation(approved_file)`。
- Learn gaps：`engines/learn/trends.py:TrendSenser.detect_gaps`。
- Token 追踪：`token_optimizer/session_tracker.py:SessionTracker` + `token_optimizer/anatomy.py:AnatomyIndex`。
- agent 注册：`engines/collaborate/orchestrator.py:get_available_agents`（→ `dispatcher.get_registered_agents()`）。
- Cedar 热加载：`adapters/crypto/cedar_policy.py:CedarPolicyEngine.reload`（AC-SEC-5 已实现）。
- workspace 原语：`db/migrations.py` migration v8（workspace_id + user_workspace_auth）。

## 关联
- PRD: `docs/prd/PRD-intelligence-adaptation-v1.5.0.md`
- 上游复盘: `.csp/artifacts/retrospective-v1.4.0.md`（findings H1-H5）
- 复用 PMS: `PMS-observability.md`（trace/health 复用）、`PMS-security-hardening.md`（Cedar/RBAC 复用）、`PMS-test-gate.md`（coverage 棘轮）
- CMS: `CODE-MODULE-SPEC.md` §M11(collaborate) / §M13(learn) / §M14(token_optimizer)
- 下游 Spec: [待 03 回填] —— F-I-1..4 各 1 Spec + F-debt 4 task
