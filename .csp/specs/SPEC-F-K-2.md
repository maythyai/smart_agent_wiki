---
id: SPEC-F-K-2
title: scope 传播清理（显式 workspace_id 参数）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-04"
prd_ref: docs/prd/PRD-graph-workspace-v1.7.0.md
pms_ref: .csp/product-spec/PMS-graph-workspace.md
feature_id: F-K-2
complexity: S
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-K-2]
---

# SPEC-F-K-2: scope 传播清理

## 实现 delta（ground 自源码）
- v1.6.0（T-F-J-1）QueryEngine.__init__ 用 `setattr(_sub, "_workspace_id", ws)` 同步 tree_mode/compiler（`engines/query/engine.py`）。
- 本轮：改 tree_mode.search / compiler.compile 接受显式 `workspace_id` 参数；QueryEngine 调用透传（`self._tree_mode.search(q, workspace_id=self._workspace_id)` / `self._compiler.compile(q, ..., workspace_id=...)`）。去 setattr 块。
- tree_mode/compiler 的 `__init__` workspace_id 可保留（用于非 engine 调用者）或移除——保留更兼容。

## 接口契约
- 内部签名变更：tree_mode.search +compiler.compile +workspace_id 参数（默认 'default'）。
- 无 setattr 子服务私有属性。

## 后端逻辑
- engine._tree_query → tree_mode.search(q, workspace_id=self._workspace_id)
- engine._nl_query → compiler.compile(q, ..., workspace_id=self._workspace_id)

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-ARCH-1（无 setattr 私有属性） | `tests/unit/test_scope_propagation.py`（新建）：assert tree_mode/compiler 收到 workspace_id（mock 调用）+ grep 源码无 setattr |

## 实现就绪度
- [x] v1.6.0 setattr 块可移除
- [x] AC 覆盖 1/1
