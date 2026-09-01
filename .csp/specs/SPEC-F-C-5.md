---
id: SPEC-F-C-5
title: 前后端 token 同源核验与补齐
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-security-hardening.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-C-5
complexity: M
tdd_ref: .csp/tech-design/SECURITY-ARCHITECTURE.md
related_modules: [API-OVERVIEW.md]
ac_coverage: 2/2
---

# SPEC-F-C-5: 前后端 token 同源

## 实现 delta（源自 CMS §M08，drift D3）
- 后端已统一（`drivers/web/routes/auth.py:13` 复用 `AuthService/JWTHandler`）。
- 实机核验前端 token 流（登录→存→带 token 请求→后端互验）；缺同源 → 补齐；缺口标 [TBD]。

## 接口契约
- `POST /api/auth/login`（:152）→ TokenPair；`POST /api/auth/refresh`（:205）。
- 前端存 token 后请求带 `Authorization: Bearer <access>`。

## 测试映射
| AC | 用例 |
|---|---|
| 前端 token 与后端 AuthService 同源互验 | `test_frontend_token_interop` |
| 后端统一（已核验）→ 前端缺口标注 [TBD] | `test_backend_auth_unified` |

## 实现就绪度
- [x] AC 覆盖 2/2
- [TBD] 前端 token 互通实机核验后定补齐范围
