# Tech Decisions Summary — 供下游消费

> 棕地硬化项目，选型 = 复用既有栈 + 4 ADR 留档。无新触发维度需选型。

## 决策清单
| ADR | 维度 | 决策 | 状态 | 关联 Feature |
|---|---|---|---|---|
| ADR-001 | 语言/框架 | Python 3.11 + Typer + FastAPI + FastMCP 复用 | Accepted | A1-6, D1-3, C* |
| ADR-002 | DB/搜索 | SQLite + FTS5 + Write Queue outbox 复用 | Accepted | A1-3, C2, C3 |
| ADR-003 | 可观测 | 自建 JSON log + trace_id middleware 复用 | Accepted | D1-3, E3 |
| ADR-004 | 安全 | JWT/Cedar/Ed25519 receipt/限流/URL guard 复用 | Accepted | C1-5 |

## 复用原则
- 全栈既有（六角架构/write_queue/observability/RBAC/receipt/FTS5），硬化只补"有模块→全链路闭环"。
- 每处设计 reference CMS 入口点（标注"源自 CMS"），不重复 spec 已有 schema/API。

## 选型门控
- [x] 触发维度全覆盖（needs_database/queue/ai/realtime/search/file_storage 全由既有承载）
- [x] ADR ≥3（4 份）
- [x] 一致性（无新框架冲突）
- [x] NFR 匹配

## [TBD] 留尾
- 覆盖率基线（F-E-1 实测后定阈值）
- 前端 token 互通（F-C-5 实机核验）
- receipt 覆盖率（F-C-2 核验）
- 备份/SLA/告警通道（运维 [TBD]，非本硬化范围）
