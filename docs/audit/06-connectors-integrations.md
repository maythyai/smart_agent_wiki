# Connectors 集成连接器 可用性启发式评估报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent
> 审查范围: `src/saw/connectors/*`、`src/saw/api/{integrations,webhooks,webhook_inbound,oauth_callback,sync,connector_settings,notion}.py`、`web/src/pages/{Integrations,ConnectorSettings}.tsx`
> 覆盖缺口: `api/{github,github_webhook,logseq,notion_sync}.py` 与前端集成组件未读（工具降级），需补审。

## 1. 执行摘要
- 框架层设计合理（协议、注册、限流、重试、加密、签名验证、背压），但关键集成接线缺失：冲突检测未接入同步、健康监控未接入同步、token 刷新未在同步前检查、Webhook 事件不处理、多连接器方法为 stub，且有 3 个阻断性崩溃。
- 核心功能完成度约 **55%**。

## 3. 核心功能完成度
| 功能点 | 状态 | 证据 |
|---|---|---|
| 连接器框架 | 完整 | connectors/* 根级 |
| Notion/GitHub/Slack/Feishu/Logseq | 部分 | connector.py 各 |
| 冲突检测接入同步 | 缺失 | F-CONN-04 |
| 健康监控接入同步 | 缺失 | F-CONN-05 |
| Webhook 事件处理 | 断裂 | F-CONN-06 |
| token 解密 | 崩溃 | F-CONN-01 |

## 4. Findings 列表

### F-CONN-01 — TokenEncryption() 无参调用
- **P0** | 严重度 4 | 置信度 high | **原则** #1
- **位置**: Notion/GitHub 连接器（`TokenEncryption()` 调用）
- **问题**: `__init__` 需要 `Fernet` 参数，但调用无参 → 同步时 token 解密 TypeError 崩溃。

### F-CONN-02 — PyGithub 缺失回退 MagicMock
- **P0** | 严重度 3 | **原则** #1/#2
- **问题**: GitHub 连接器在 PyGithub 未装时回退 `MagicMock()`，用户看到假数据无提示。

### F-CONN-03 — 对同步方法 await
- **P0** | 严重度 3 | **原则** #1
- **位置**: `api/integrations.py`、`api/connector_settings.py`
- **问题**: 对同步方法 `get_authorization_url` 使用 `await` → 重新授权端点必然 500。

### F-CONN-04 — ConflictResolver 未接入同步
- **P1** | 严重度 2 | **原则** #1
- **问题**: `SyncEngine.sync_pull/sync_push` 不调用冲突检测。

### F-CONN-05 — HealthMonitor 未接入同步
- **P1** | 严重度 2 | **原则** #1
- **问题**: 同步流程不调用 `record_success/record_failure`。

### F-CONN-06 — Webhook 入站不处理为 Claim
- **P1** | 严重度 3 | **原则** #1
- **问题**: 仅确认接收不处理，推送式数据接入断裂。

### F-CONN-07 — OAuth 不处理拒绝授权
- **P1** | 严重度 2 | **原则** #9
- **问题**: 用户拒绝授权返回 422 而非友好错误。

### F-CONN-08 — 同步内联执行
- **P1** | 严重度 2 | **原则** #1
- **问题**: 长同步在请求内联执行会超时。

### F-CONN-09 — trigger_all_syncs 无操作
- **P1** | 严重度 3 | **原则** #1/#9
- **问题**: 声称触发但实际什么都不做。

### F-CONN-10 — OAuth 授权 URL 未 URL 编码
- **P1** | 严重度 2 | **原则** #5

## 5. 严重度分布
| 严重度 | 数量 |
|---|---|
| 4 | 1 |
| 3 | 4 |
| 2 | 6+ |
| 优先级 | P0×3 P1×7 P2×6 P3×1（约） |

## 6. 修复优先级
- **Foundation**: F-CONN-01/02/03
- **Core UI**: F-CONN-04/05/06/09
- **Interactions & States**: F-CONN-07/08/10
- **Polish**: 其余

## 7. 下一步建议
- 补审 github/logseq/notion_sync API + 前端；修 token 解密与 await 同步方法；接入冲突检测/健康监控；Webhook 事件入 Claim。
