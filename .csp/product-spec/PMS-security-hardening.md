---
type: module-spec
confidence: high
sources:
  - "[[docs/prd/PRD-product-hardening-v1.md]]"
  - "[[.csp/code-spec/saw/CODE-MODULE-SPEC.md]]"
seeAlso:
  - "[[code-spec/saw/CODE-MODULE-SPEC.md]] §M08"
created: "2026-09-01"
updated: "2026-09-01"
---

# PMS: security-hardening（安全基础深化）

## 模块边界
- **做什么**：把已存在的 RBAC/限流/Ed25519 审计 receipts 从"有模块"深化为"全链路闭环可验收"——权限矩阵全覆盖、receipt 链式不断裂、限流双轨生效、输入消毒覆盖外部 URL 入口、前后端 token 同源。
- **不做什么**：不重写已有 `auth/`、`adapters/crypto/`、`api/rate_limit.py`（既有实现复用）；不定义加密算法选型（HOW）。前端 token 互通现状 [TBD] 待实机核验后补。
- **PMS 边界=PRD §3.3**。

## 验收形态
- 安全自检：0 裸 write/敏感 read 路由（以 `app.py` include_router auth_dep 为校验源）。
- receipt：所有 agent 操作 + write_queue 变更产出 Ed25519 receipt，`prev_receipt_id` 链不断裂。
- 限流：超 100/h（默认，env 可覆盖）→ 429 + Retry-After。
- URL 守卫覆盖所有外部 URL 入口。

## 接口契约摘要
- 鉴权依赖：`auth_dep`（`drivers/web/app.py:267`）挂在 protected 路由。
- receipt：`adapters/crypto/ed25519.py` `ReceiptSigner`（`ed25519.py:63`）。
- 权限：`auth/permissions.py` `PermissionService`（`:59`，Cedar 引擎）。
- 限流：`api/rate_limit.py` `RateLimitConfig`（`:24`，100/h、1000/d）。
- 前端 token：与 `AuthService` 同源 `[TBD]`。

## 关联
- PRD: `docs/prd/PRD-product-hardening-v1.md` §3.3
- CMS: `CODE-MODULE-SPEC.md` §M08（drift D3 后端已解，前端 [TBD]）
- 下游 Spec: [待 03 回填]
