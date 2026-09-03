---
id: SPEC-F-J-1
title: workspace 读取路径全路由（tree_mode + compiler）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-03"
prd_ref: docs/prd/PRD-debt-closure-v1.6.0.md
pms_ref: .csp/product-spec/PMS-debt-closure.md
feature_id: F-J-1
complexity: M
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-J-1]
---

# SPEC-F-J-1: tree_mode + compiler workspace 注入

## 实现 delta（ground 自源码）
- `TreeModeSearch.__init__`（`engines/query/tree_mode.py:58`）加 `workspace_id: str = "default"`；`search` 内 `claims_repo.get_by_id(doc_id)` → `get_by_id(doc_id, workspace_id=self._workspace_id)`（line 108/243/250）。
- `ContextCompiler.__init__`（`engines/query/compiler.py:41`）加 `workspace_id`；`compile` 内 `get_by_id(uuid)` → `get_by_id(uuid, workspace_id=...)`（line 88）。
- `QueryEngine` 已持 workspace_id（v1.5.0）；构造 tree_mode/compiler 时透传 `workspace_id=self._workspace_id`（`create_app_from_config` + `query_cmd.py` 装配点）。
- repo 方法 `get_by_id(uuid, workspace_id)` v1.5.0 已支持 → **不改 repo**。

## 接口契约
- 无新 CLI/HTTP；内部签名变更（tree_mode/compiler __init__ +workspace_id，默认 'default' backward compat）。
- 跨 ws：A ws claim 不在 B ws tree/compile 结果。

## 后端逻辑
- tree_mode.search → FTS5 → get_by_id(doc_id, ws) → 非 ws 的 claim 返回 None → 不入 SectionPath。
- compiler.compile → search → get_by_id(uuid, ws) → 非 ws claim 不入 context。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-WS-4（tree/compile 跨 ws 隔离） | `tests/unit/test_workspace_routing.py` 扩：tree_mode + compiler 在 ws B 不返 ws A claim |

## 实现就绪度
- [x] repo.get_by_id(workspace_id) v1.5.0 就绪
- [x] AC 覆盖 1/1
