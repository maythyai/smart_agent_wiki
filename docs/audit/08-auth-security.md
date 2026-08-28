# Auth 与安全 可用性启发式评估报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent
> 审查范围: `src/saw/auth/*`、`drivers/web/middleware/security.py`、`drivers/web/routes/auth.py`、`api/{keys,rate_limit}.py`、`adapters/crypto/*`、`web/src/stores/authStore.ts`、`web/src/pages/Login.tsx`
> 独立复核: F-AUTH-01 已由主审读取 `auth.py:29` 确认（`role` pattern 含 `admin`，`register()` :77 直接采用）。

## 1. 执行摘要
- 后端登录/注册/刷新/登出链路完整，Ed25519 签名与密钥文件管理完善，安全头齐全，但存在**权限提升级**漏洞（注册可自选 admin）、前端无 token 自动刷新、无注册页、两套 require_role 不一致。
- 核心功能完成度约 **65%**。

## 3. 核心功能完成度
| 功能点 | 状态 | 证据 |
|---|---|---|
| 登录/刷新/登出 | 完整 | auth.py + jwt_auth.py |
| Ed25519 签名 | 完整 | crypto/ed25519.py |
| RBAC | 部分 | 两套 require_role（F-AUTH-05） |
| 前端 token 刷新 | 缺失 | F-AUTH-02 |
| 注册（Web） | 缺失 | F-AUTH-04 |

## 4. Findings 列表

### F-AUTH-01 — 注册允许自选 admin 角色（权限提升）
- **P0** | 严重度 4 | 置信度 high（已独立复核） | **原则** #5
- **位置**: `drivers/web/routes/auth.py:29`（`RegisterRequest.role` pattern=`^(admin|editor|viewer)$`）+ `:77` `register()` 用 `request.role` + `:96` 存 `request.role`
- **问题**: 任意未认证用户可注册为 admin。
- **修复**: 注册强制 `role=viewer`，admin 提升另走特权接口；或移除 `admin` 出 pattern。

### F-AUTH-02 — 前端无 token 自动刷新
- **P0** | 严重度 4 | **原则** #1/#3
- **位置**: `web/src/stores/authStore.ts:1-55`
- **问题**: access token 30 分钟过期后无拦截器自动刷新，用户被无声登出且无引导。

### F-AUTH-03 — 登录用户枚举（时序差异）
- **P1** | 严重度 3 | **原则** #5
- **问题**: 用户不存在时立即 401，密码错误时执行 bcrypt（~100ms），可枚举用户。

### F-AUTH-04 — 注册仅 CLI 可用，Web 无注册页
- **P1** | 严重度 3 | **原则** #9
- **问题**: Login.tsx 指向 `saw auth register` CLI，对无 CLI 权限用户是死胡同。

### F-AUTH-05 — 权限不足反馈暴露内部角色名
- **P1** | 严重度 2 | **原则** #2/#9
- **问题**: 403 返回 `Requires one of roles: admin, editor`，用户无法理解；且存在两套不一致 require_role。

### F-AUTH-06 — InputSanitizer 仅查 query 不查 body
- **P1** | 严重度 3 | **原则** #5
- **问题**: `sanitize_string` 定义但从未调用，body 不清洗。

### F-AUTH-08 — 429 无 Retry-After 头
- **P1** | 严重度 2 | **原则** #9
- **问题**: `retry_after` 数值无单位标注。

### F-AUTH-09 — 前端密码无 minLength 校验
- **P1** | 严重度 2 | **原则** #5
- **问题**: 短密码得到误导性 "Invalid email or password"。

## 5. 严重度分布
| 严重度 | 数量 |
|---|---|
| 4 | 2 |
| 3 | 4 |
| 2 | 7 |
| 1 | 5 |
| 优先级 | P0×2 P1×7 P2×6 P3×3 |

## 6. 修复优先级
- **Foundation**: F-AUTH-01/02
- **Core UI**: F-AUTH-03/04/05/06
- **Interactions & States**: F-AUTH-08/09
- **Polish**: 其余

## 7. 下一步建议
- 立即修 F-AUTH-01（权限提升）；前端加 token 刷新拦截器；统一 require_role；注册页或明确 CLI-only 引导。
