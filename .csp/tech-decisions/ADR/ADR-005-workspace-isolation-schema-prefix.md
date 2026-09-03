# ADR-005: 多工作空间隔离方案（schema 前缀 vs 分库）

## 状态：Accepted
## 上下文
v1.4.0 platform-team track 需多工作空间隔离（F-P-4）：单实例多 wiki workspace，数据物理隔离，用户授权绑定 workspace（AC-WS-1/AC-WS-2）。既有 DB 是单 SQLite（`claims.db`，migration v1..v7）。需选隔离机制。

## 决策
**schema 前缀（单 DB，workspace_id 列）**：所有业务表加 `workspace_id TEXT NOT NULL` 列 + 复合索引，查询路由层注入 workspace_id 过滤。workspace 授权绑定存新表 `user_workspace_auth`（migration v8）。不建多 DB 文件。

## 备选方案
| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| schema 前缀（单 DB + workspace_id 列） | 迁移成本低（v8 加列）、复用既有 conn/repo、查询路由简单 | 单 DB 共享（理论跨 ws 查询风险，靠路由层 + 索引守） | 中小团队多 ws ✓ |
| 分库（每 workspace 一 DB 文件） | 物理强隔离 | conn 池/迁移/migration 管理复杂、VaultRepository 绑 path 需重写 | 大租户/合规强隔离 |
| schema 前缀 + 行级 Cedar | 策略即代码守隔离 | Cedar 不能管 SQLite 行级（应用层守） | 已有 Cedar 但 DB 层不强制 |

## 理由
需求匹配（多团队共存的隔离基座，非 SaaS 强隔离）40% + 成本（加列 vs 重写 repo/conn 池，v8 一次迁移）30% + 运维（单 DB 备份/运维简单）20% + 团队 10%。F-P-4 明确"本轮只做隔离基座 + 绑定，不做计费/配额"，schema 前缀足够。分库留 v2.0 SaaS 强隔离。

## 后果
- 正：v8 一次 migration 加列；既有 repo 复用；workspace 路由在应用层（PermissionService scope 已绑 user→workspace）。
- 负：DB 层不强制行隔离，靠应用层路由 + e2e 测试守（AC-WS-1/2）；跨 ws 查询须显式 workspace_id 过滤（漏过滤=数据泄露，靠 F-P-1 e2e 守卫）。
- 风险：既有数据无 workspace_id —— v8 default 一个 `default` workspace_id（向后兼容单机 local-first）。

## 关联 Feature
F-P-4（多工作空间隔离）、F-P-1（RBAC 授权 scope 绑 workspace）、migration v8
