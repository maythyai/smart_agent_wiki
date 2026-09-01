---
id: SPEC-F-C-1
title: 权限矩阵全覆盖（裸路由检测）
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-security-hardening.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-C-1
complexity: M
tdd_ref: .csp/tech-design/SECURITY-ARCHITECTURE.md
related_modules: [API-OVERVIEW.md]
ac_coverage: 2/2
related_tasks: [.csp/tasks/WBS.md#T-F-C-1-1]
---

# SPEC-F-C-1: 权限矩阵全覆盖

## 实现 delta（源自 CMS §M08）
- 安全自检脚本：扫 `drivers/web/app.py` include_router 装配，检测 write/敏感 read 路由是否挂 `auth_dep`（:267）；覆盖 `api/` 与 `drivers/web/routes/` 双轨。
- 复用 `PermissionService`（`auth/permissions.py:59` + Cedar）；输出权限矩阵（角色×功能×数据范围）文档。

## 接口契约
- CLI/脚本：`saw security-check routes` [TBD]；输出裸路由清单 + 退出码。

## 后端逻辑
- 解析 include_router + APIRouter prefix → 列 protected/public → 裸 write 路由 = FAIL。

## 测试映射
| AC | 用例 |
|---|---|
| AC-SEC-1（0 裸路由） | `test_no_unprotected_write_routes` |
| protected 路由挂 auth_dep | `test_auth_dep_attached` |

## 实现就绪度
- [x] AC 覆盖 2/2
