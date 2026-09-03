---
id: SPEC-F-J-4
title: policy reload Web admin 端点
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-03"
prd_ref: docs/prd/PRD-debt-closure-v1.6.0.md
pms_ref: .csp/product-spec/PMS-debt-closure.md
feature_id: F-J-4
complexity: S
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-J-4]
---

# SPEC-F-J-4: policy reload Web admin 端点

## 实现 delta（ground 自源码）
- v1.5.0（T-F-Z-8）落了 `saw policy reload` CLI；Web admin 端点 defer（I4）。
- 新增 `POST /api/admin/policy/reload` 路由（`drivers/web/routes/` 或 `api/routes/`），admin-only（`Depends(require_role("admin"))`）。
- 复用 `CedarPolicyEngine.reload()`（`adapters/crypto/cedar_policy.py`，AC-SEC-5 已实现）；从 `app.state.cedar` 取实例（v1.4.0 P-1 已在 create_app 装配 cedar）。
- 无 policy 文件时返回 200 + "no policy"（与 CLI 一致）。

## 接口契约
- `POST /api/admin/policy/reload` → 200 `{backend, reloaded}`；非 admin → 403。
- 复用既有 auth_dep + require_role。

## 后端逻辑
- route → app.state.cedar.reload() → 返回 backend + 结果。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-SEC-6（admin 触发，非 admin 403） | `tests/unit/test_policy_reload_cmd.py` 扩或 `test_admin_policy_reload.py`：admin 200 + 非 admin 403 + cedar.reload 调用 |

## 实现就绪度
- [x] cedar.reload() + app.state.cedar 就绪
- [x] require_role 就绪
- [x] AC 覆盖 1/1
