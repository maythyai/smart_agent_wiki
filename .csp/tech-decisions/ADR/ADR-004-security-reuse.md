# ADR-004: 安全复用（JWT + RBAC/Cedar + Ed25519 receipt + 限流 + URL guard）

## 状态：Accepted
## 上下文
SAW 已有完整安全栈：JWT 双 token + bcrypt（`auth/jwt_auth.py`）、RBAC + Cedar Policy（`auth/permissions.py:59` + `cedar_policy.py`）、Ed25519 receipt（`adapters/crypto/ed25519.py:63` ReceiptSigner）、限流（`api/rate_limit.py:24`）、URL 守卫（`adapters/url_guard.py`）。硬化目标"有模块→全链路闭环可验收"。
## 决策
复用既有安全栈。F-C-1 权限矩阵全覆盖（裸路由检测）；F-C-2 receipt 全链路闭环（agent + write_queue 变更）；F-C-3 限流双轨（429+Retry-After）；F-C-4 URL 守卫全覆盖；F-C-5 前后端 token 同源核验。不引入新加密/鉴权库。
## 备选方案
| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| 复用 JWT/Cedar/Ed25519 | 已建，零迁移 | — | 棕地硬化 ✓ |
| OAuth2/OIDC 外部 IdP | 标准化 | 破 local-first 单机 | 多租户 SaaS |
| 引入 PASETO | 更现代 token | 既有 JWT 可用，无收益 | 绿地 |
## 理由
需求匹配（local-first + 既有全栈 + 可审计）40% + 团队 20% + 生态 15% + 运维（无外部 IdP）15% + 成本 10%。Cedar 提供策略即代码，Ed25519 链式 receipt 满足审计闭环。
## 后果
- 正：receipt 链式不可篡改；RBAC 矩阵可验。
- 负：前端 token 互通现状 [TBD]（F-C-5 实机核验后补）。
- 风险：receipt 覆盖率 [TBD]（F-C-2 核验后补）。
## 关联 Feature
F-C-1..5（全部安全硬化）、F-A-5（离线 fallback 不涉鉴权）
