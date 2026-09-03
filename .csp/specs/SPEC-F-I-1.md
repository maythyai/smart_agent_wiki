---
id: SPEC-F-I-1
title: workflow CLI（run/validate/resume/status）+ INTERRUPTED 续跑
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-03"
prd_ref: docs/prd/PRD-intelligence-adaptation-v1.5.0.md
pms_ref: .csp/product-spec/PMS-intelligence-adaptation.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-I-1
complexity: M
adr_ref: .csp/tech-decisions/ADR/ADR-006-workflow-resume-state-machine.md
ac_coverage: 2/2
related_tasks: [.csp/tasks/WBS.md#T-F-I-1]
---

# SPEC-F-I-1: workflow CLI + resume

## 实现 delta（ground 自源码）
- 新增 `drivers/cli/commands/workflow_cmd.py`（Typer sub-app：run/validate/resume/status/lint），`main.py` 注册 `app.add_typer(workflow_app, name="workflow")`。
- 引擎层复用：`engines/collaborate/workflow_executor.py:WorkflowExecutor`（M-16 状态机 + HI-9 `_persist_workflow`）+ `workflow_parser.py:WorkflowParser`。**不改既有 execute 路径**。
- 新增 `WorkflowExecutor.resume(workflow_id)`：从 `workflow_executions` 读行，校验 state machine 允许 INTERRUPTED/FAILED/TIMEOUT→RUNNING（`validate_workflow_transition`），从 `steps_completed` index 续跑。context 重建见 ADR-006（index-based，丢则该步重跑）。
- `resume` 需要 dispatcher/a2a/governor/conn 装配——复用 `web_cmd`/`mcp_cmd` 既有装配或建轻量 `bootstrap_runtime()` helper（[TBD] 抽取共用）。

## 接口契约
- `saw workflow run <def.yaml> [--input KEY=VAL]...` → 执行，打印 workflow_id + status + steps。
- `saw workflow validate <def.yaml>` → schema 校验（parse + `validate(available_agents)`），失败明确报错退出 1。
- `saw workflow resume <workflow_id>` → 续跑 interrupted/failed。
- `saw workflow status <workflow_id>` → 查 `workflow_executions` 行。
- 无新增 HTTP（CLI surface only）。

## UI/DB
- DB：复用 `workflow_executions` 表（migration v4，零新 migration）。
- 字段：workflow_id/definition_name/status/steps_completed/steps_total/errors_json/updated_at/finished_at。

## 后端逻辑
- run：parse → persist(running) → execute_definition（timeout/gate/retry/fallback 既有）→ persist(completed/failed/timeout)。
- resume：SELECT row → guard transition → re-execute from steps_completed index → persist。
- validate：parse + agent 存在性 + gate 语法（既有 `WorkflowParser.validate`）。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-WF-1（run + crash 可恢复） | `tests/unit/test_workflow_cmd.py:run_executes` + `resume_after_interrupt`：注入 interrupted 行→resume→completed |
| AC-WF-2（schema 校验失败报错） | `validate_invalid_yaml`：缺 name/steps/未知 agent → 退出 1 + 明确错 |

## 实现就绪度
- [x] 引擎层全就绪（executor/parser/state machine/recovery）
- [x] AC 覆盖 2/2
- [TBD] runtime bootstrap 抽取（dispatcher/a2a 装配复用）
