# Tech Design Summary — TDD 汇总（供下游消费）

> 棕地硬化，TDD ground 在 CMS。架构/数据/接口/安全均复用既有，本设计标注硬化 delta。

## 系统架构
六角架构 domain→engines→adapters→drivers；三入口（Typer/FastAPI/FastMCP）；Write Queue 唯一变更网关。5 域边界对齐 PMS。详见 `ARCHITECTURE-DESIGN.md`。

## 数据架构
单 SQLite + FTS5，四层存储；Write Queue outbox 保证 mutation 不丢；查询只读不经 outbox。详见 `DATA-ARCHITECTURE.md`。

## 接口架构
REST `/api/v1/*` + WebSocket + MCP stdio；JWT 中心鉴权；统一错误格式；限流 100/h+1000/d。路由双轨保留（不重构）。详见 `INTERFACE-ARCHITECTURE.md`。

## 安全架构
JWT/Cedar/Ed25519 receipt/限流/URL guard 全复用；STRIDE 6 威胁均有缓解映射。详见 `SECURITY-ARCHITECTURE.md`。

## 关键难点
1. 离线 fallback（规则 fallback 复用，S）
2. trace_id 贯穿（contextvar，M）
3. 路由双轨（保留+自检覆盖，S）
4. 覆盖率门禁基线（实测后定，M）
详见 `KEY-CHALLENGES.md`。

## 多方案对比
每难点 ≥2 候选已对比 + 推荐 + 理由（见 KEY-CHALLENGES）。

## TDD 门控
- [x] 系统架构（模块+拓扑，对齐 PMS，源自 CMS）
- [x] 数据架构（ER+数据流+一致性）
- [x] 接口架构（风格+版本+鉴权）
- [x] 安全架构（STRIDE+缓解）
- [x] 每难点有方案
- [x] ≥2 决策多方案对比
- [x] 与 tech-decisions 一致；关键决策标注 CMS 出处

## [TBD] 留尾
路由双轨统一（后续）、CLI/MCP trace 贯穿（V1.1）、PII 加密/日志脱敏/服务间 API Key/备份 SLA（运维）。
