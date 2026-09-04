---
id: SPEC-F-M-1
title: workflow list durable（saw workflow list）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-04"
prd_ref: docs/prd/PRD-agent-viz-v1.9.0.md
pms_ref: .csp/product-spec/PMS-agent-viz.md
feature_id: F-M-1
complexity: S
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-M-1]
---

# SPEC-F-M-1: saw workflow list

## 实现 delta（ground 自源码）
- `drivers/cli/commands/workflow_cmd.py`（v1.5.0 既有 sub-app）加 `list` 子命令。
- 查 `workflow_executions` 表（v4, HI-9）最近 N 条：`SELECT workflow_id, definition_name, status, steps_completed, steps_total, updated_at, finished_at FROM workflow_executions ORDER BY updated_at DESC LIMIT ?`。
- bootstrap 复用 `_bootstrap_runtime`（claims.db + apply_migrations）——但只需 conn，不需 dispatcher/a2a。为减负，`list` 只开 conn（不走完整 collab 装配）。
- **与 REST `/api/v1/workflows` 互补**：REST = in-memory live（重启丢）；CLI list = DB durable 历史。

## 接口契约
- `saw workflow list [--limit 20] [--path .]` → 表（id/name/status/steps/updated）；exit 0（空也报告）。

## 后端逻辑
- open claims.db → apply_migrations → SELECT recent → Rich table。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-WF-3（list 输出最近运行） | `tests/unit/test_workflow_cmd.py` 扩：seed 2 行 → list → 含两行 + 排序 |

## 实现就绪度
- [x] workflow_executions v4 表就绪
- [x] AC 覆盖 1/1
