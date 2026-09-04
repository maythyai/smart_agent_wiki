---
id: SPEC-F-K-1
title: graph workspace 隔离（migration v9 + 读写）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-04"
prd_ref: docs/prd/PRD-graph-workspace-v1.7.0.md
pms_ref: .csp/product-spec/PMS-graph-workspace.md
feature_id: F-K-1
complexity: M
adr_ref: .csp/tech-decisions/ADR/ADR-009-entity-workspace-isolation.md
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-K-1]
---

# SPEC-F-K-1: graph workspace 隔离

## 实现 delta（ground 自源码）
- migration v9：`db/migrations.py:_register(9, _add_entity_workspace)` → entity 表加 `workspace_id` 列 + index（default 'default'）。
- Entity domain：加 `workspace_id: str = "default"` 字段（镜像 Claim）。
- 写：IngestPipeline stamp `validated.valid_entities` workspace_id（同 F-J-2 claims）；GraphSink INSERT entity 带 workspace_id 列（`graph_sink.py:47`）。
- 读：`GraphTraverse.__init__` 加 `workspace_id`；`_load_graph` entity SQL `WHERE workspace_id=?`；relation SQL 加两端 entity workspace 过滤。
- QueryEngine：构造 GraphTraverse 时透传 workspace_id（`create_app_from_config` + `query_cmd.py`）。

## 接口契约
- 无新 CLI/HTTP；内部签名变更（GraphTraverse __init__ +workspace_id，默认 'default' backward compat）。
- 跨 ws：A ws entity 不在 B ws 图遍历结果。

## 后端逻辑
- _load_graph：`SELECT ... FROM entity WHERE workspace_id=?` + relation 两端 `JOIN entity` 过滤。
- ingest stamp + GraphSink persist + graph_traverse filter。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-WS-6（graph 跨 ws 隔离） | `tests/unit/test_graph_workspace.py`（新建）：A ws entity/relation 在 B ws traverse 返回空 |

## 实现就绪度
- [x] claim 模式（ADR-007/008）可镜像
- [x] AC 覆盖 1/1
- migration v9 串行 Wave 1
