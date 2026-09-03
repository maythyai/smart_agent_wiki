---
id: SPEC-F-I-4
title: agent 角色一致性 lint
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-03"
prd_ref: docs/prd/PRD-intelligence-adaptation-v1.5.0.md
pms_ref: .csp/product-spec/PMS-intelligence-adaptation.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-I-4
complexity: S
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-I-4]
---

# SPEC-F-I-4: agent 角色一致性 lint

## 实现 delta（ground 自源码）
- 复用 `engines/collaborate/workflow_parser.py:WorkflowParser.validate(workflow, available_agents)`（已检 `step.agent in available_agents` + gate 语法）。
- `available_agents` 取自 `engines/collaborate/orchestrator.py:get_available_agents()`（→ `dispatcher.get_registered_agents().keys()`，6 既有角色：writer/librarian/critic/linker/scholar/guardian）。
- 新增 `saw workflow lint <def.yaml>`（在 F-I-1 workflow_cmd sub-app 内，同文件）→ parse + validate(registered_agents) → 输出 errors 列表，退出 0/1。
- **不引新 lint 引擎**：复用 parser.validate，避免重复实现。

## 接口契约
- `saw workflow lint <def.yaml>` → 0 未知角色=exit 0；有未知角色/gate 语法错=exit 1 + 行号错。

## UI/DB
- N/A。

## 后端逻辑
- parse → get_available_agents → validate → 报错。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-AG-1（声明 agent ∈ 注册集） | `tests/unit/test_workflow_lint.py`：valid yaml→exit 0；含未知 agent→exit 1 + 定位 step |

## 实现就绪度
- [x] parser.validate + get_available_agents 全就绪
- [x] AC 覆盖 1/1
- 与 F-I-1 同 workflow_cmd.py 文件（bundle 提交，不并行 split）
