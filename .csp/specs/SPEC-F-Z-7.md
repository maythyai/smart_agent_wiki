---
id: SPEC-F-Z-7
title: workspace 全查询路径路由
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-03"
prd_ref: docs/prd/PRD-intelligence-adaptation-v1.5.0.md
pms_ref: .csp/product-spec/PMS-intelligence-adaptation.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-Z-7
complexity: L
adr_ref: .csp/tech-decisions/ADR/ADR-007-workspace-scope-injection.md
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-Z-7]
---

# SPEC-F-Z-7: workspace scope 注入

## 实现 delta（ground 自源码）
- migration v8 已给 `claim.workspace_id`（default 'default'）+ `user_workspace_auth`。但 `QueryEngine`（`engines/query/engine.py`）/`IngestPipeline`（`engines/ingest/pipeline.py`）/claims repo search/get/list **无 workspace_id 过滤**（grep 确认 0 命中）。
- 注入点 = repo 层（ADR-007）：`ClaimsRepository` search/get/list/save 加 `workspace_id: str = "default"`，SQL 加 `AND workspace_id = ?`。
- `QueryEngine` 构造持 `workspace_id`，透传 repo 调用。`IngestPipeline` 入库时带 session workspace_id 写 claim。
- default 'default' 保单机兼容（既有调用不破坏）。

## 接口契约
- 无新 CLI/HTTP；内部签名变更（repo 方法 +workspace_id 参数）。
- 跨 workspace 查询：A ws claim 在 B ws search 返回空（e2e 验）。

## UI/DB
- DB：零新 migration（复用 v8 workspace_id 列）。

## 后端逻辑
- repo.search(question, workspace_id) → SQL `... AND workspace_id = ?`。
- engine 持 ws，所有 repo 调用透传。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-WS-3（全路径 workspace 隔离） | `tests/unit/test_workspace_routing.py`：A ws 写 claim → B ws search 返回空；default ws 既有数据可查（兼容） |

## 实现就绪度
- [x] v8 原语就绪（列 + 绑定表 + index）
- [x] AC 覆盖 1/1
- [TBD] 逐 repo 方法核防漏（lint 核签名 + e2e 守）
- 串行 Wave 2（多 repo 改动，防并行冲突）
