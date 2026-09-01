# Security Architecture — 安全架构（源自 CMS §M08）

## 安全分层
| 层 | 措施 | 既有 | 硬化 Feature |
|---|---|---|---|
| 网络 | URL 守卫防 SSRF/协议混淆 | `adapters/url_guard.py` | F-C-4 全覆盖 |
| 应用 | 限流防刷 | `api/rate_limit.py:24` | F-C-3 双轨 |
| 认证 | JWT 双 token + bcrypt | `auth/jwt_auth.py` | F-C-5 同源核验 |
| 授权 | RBAC + Cedar Policy | `auth/permissions.py:59` | F-C-1 矩阵全覆盖 |
| 数据 | Ed25519 receipt 链式 | `adapters/crypto/ed25519.py:63` | F-C-2 闭环 |
| 运维 | 审计 receipt + 日志脱敏 [TBD] | receipt 在 | F-C-2 |

## 威胁建模 STRIDE
| 威胁 | 示例 | 缓解 | Feature |
|---|---|---|---|
| 欺骗(Spoofing) | 伪造 token | JWT 签名验证 + bcrypt | F-C-5 |
| 篡改(Tampering) | 篡改操作记录 | Ed25519 链式 receipt | F-C-2 |
| 否认(Repudiation) | 操作可抵赖 | receipt 不可篡改 + 日志 trace | F-C-2/F-D-2 |
| 信息泄露(Info Disclosure) | 越权读 | RBAC 矩阵 + auth_dep 全挂 | F-C-1 |
| 拒绝服务(DoS) | 滥用 API | 限流双轨 429 | F-C-3 |
| 提权(EoP) | 低权角色调高权端点 | Cedar 策略 + 角色权限校验 | F-C-1 |

## 数据安全
- 前后端双重校验：后端 Pydantic schemas（`drivers/web/schemas/`）已在；前端 [TBD]。
- ORM 参数化防注入（SQLite + 参数化查询）。
- 输出编码防 XSS（Web）。
- SameSite + token 防 CSRF。
- PII 加密存储 [TBD]；日志脱敏 [TBD]；响应不含内部敏感 ID [TBD]。

## 配置与状态（三级配置）
- `config.yaml`（功能开关/参数）、`.env`（仅 secrets，不提交，有 `.env.example`）、`auth.json`（OAuth）。
- 优先级：进程环境 > 项目 .env > 全局 .env > config.yaml。
- 运行时状态 SQLite-first（JSON 存配置、SQLite 存状态）。
