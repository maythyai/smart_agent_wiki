---
id: SPEC-F-M-3
title: agent roster REST（GET /api/v1/agents）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-04"
prd_ref: docs/prd/PRD-agent-viz-v1.9.0.md
pms_ref: .csp/product-spec/PMS-agent-viz.md
feature_id: F-M-3
complexity: S
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-M-3]
---

# SPEC-F-M-3: GET /api/v1/agents

## 实现 delta（ground 自源码）
- `api/routes/collaborate.py`（既有 router，prefix=/api/v1）加 `GET /agents` 端点。
- 复用 `build_default_agents(llm_router=None)` → 返回 JSON `[{name, model_tier, tools_allowed, rule}]`。
- 鉴权：复用 router 级 auth_dep（已在 create_app include_router 加 dependencies=auth_dep）。
- `GET /api/v1/workflows` 已存在（in-memory），不动。

## 接口契约
- `GET /api/v1/agents` → `{"agents": [{name, model_tier, tools_allowed, rule}], "total": 6}`。

## 后端逻辑
- build_default_agents(None) → 遍历 → JSON。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-API-1（6 角色 JSON） | `tests/unit/test_agents_api.py`：TestClient GET → 6 角色 + Guardian rule=true |

## 实现就绪度
- [x] build_default_agents + collaborate router 就绪
- [x] AC 覆盖 1/1
