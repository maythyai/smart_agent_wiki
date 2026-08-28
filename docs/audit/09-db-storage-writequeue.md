# DB 与存储层 可用性启发式评估报告

> mode: heuristic-review · 评估日期: 2026-08-28 · 评估者: CodEva Agent
> 审查范围: `src/saw/db/*`、`src/saw/adapters/storage/*`、`src/saw/write_queue/*`
> 覆盖说明: 已读全部 db/（12 文件）、storage/（6 文件）、write_queue/{queue,dispatcher}.py。
> **独立复核**: `write_queue/sinks/` 实有 7 个 sink 文件（claims/connector/contradictions/fts5/graph/vault/wiki_sink.py），且 `drivers/web/app.py` 显式装配 WikiSink/FTS5Sink/ClaimsSink/GraphSink/ContradictionsSink。原代理 F-DB-01（"sinks 缺失"）为**工具降级导致的误报，已推翻**。

## 1. 执行摘要
- 基础设施（模型、迁移、仓储、入队/重试/死信/恢复）设计完善且实现完整，sinks 已存在并接线。剩余问题集中在运维可见性与错误上抛一致性。
- 核心功能完成度约 **80%**（原代理估 75%，扣除误报后上调）。

## 3. 核心功能完成度
| 功能点 | 状态 | 证据 |
|---|---|---|
| 表模型 + 迁移框架 | 完整 | db/migrations.py（v1–v5） |
| claims/wiki/vault/fts 仓储 | 完整 | adapters/storage/* |
| Write Queue outbox | 完整 | write_queue/queue.py |
| Dispatcher + sinks | 完整 | app.py 装配 + sinks/* |
| 死信队列监控 | 缺失 | F-DB-04 |
| 错误上抛一致性 | 部分 | F-DB-07 |

## 4. Findings 列表

### ~~F-DB-01 — sinks/ 缺失~~（误报，已推翻）
- **结论**: sinks 实际存在且在 `app.py` 装配。代理因 `list_dir`/`read_file` 降级误判。
- **状态**: REFUTED（待核 → 已核，删除）。

### F-DB-02 — 未知 sink op 无限 pending
- **P0** | 严重度 3 | **原则** #1
- **位置**: `write_queue/dispatcher.py`
- **问题**: 遇未注册 sink 时 op 保持 pending 无限重试，不进入 failed/dead_letter，无用户反馈。

### F-DB-03 — session bootstrap 失败仍 yield session
- **P0** | 严重度 3 | **原则** #9
- **位置**: `src/saw/db/session.py`（`_ensure_schema` / `get_session`）
- **问题**: schema bootstrap 失败后仍 yield session，用户看到裸 SQLAlchemy "no such table" 错误。

### F-DB-04 — 死信队列无监控
- **P1** | 严重度 2 | **原则** #1
- **问题**: `get_dead_letter` 存在但无监控/告警接入（app.py 有 60s 循环日志，但无用户面）。

### F-DB-05 — outbox 积压无告警
- **P1** | 严重度 2 | **原则** #1

### F-DB-06 — vault git 操作静默失败
- **P1** | 严重度 2 | **原则** #1
- **位置**: `adapters/storage/vault_repository.py`

### F-DB-07 — claims_repository 错误包装不一致
- **P1** | 严重度 2 | **原则** #4
- **位置**: `adapters/storage/claims_repository.py`

### F-DB-08 — UPDATE/DELETE 不检查存在性
- **P1** | 严重度 2 | **原则** #5/#9

### F-DB-09 — enqueue_atomic 无 dispatcher 时静默丢弃
- **P1** | 严重度 3 | **原则** #1
- **位置**: `write_queue/queue.py`（`enqueue_atomic`）
- **问题**: 无 attached dispatcher 时 enqueue 后无分发，写静默丢失（注：app.py 已 attach，但脱离 web 场景仍存在）。

> P2：双 schema 初始化路径无协调、fts5_utils 文档描述不存在功能、busy_timeout 可能裸锁错误、FTS5 title 列语义混淆。

## 5. 严重度分布
| 严重度 | 数量 |
|---|---|
| 4 | 0 |
| 3 | 3 |
| 2 | 7 |
| 1 | 3 |
| 优先级 | P0×2 P1×6 P2×4 P3×1（扣除误报后） |

## 6. 修复优先级
- **Foundation**: F-DB-02/03
- **Core UI**: F-DB-04/05/09
- **Interactions & States**: F-DB-06/07/08
- **Polish**: 双 schema 协调、fts5_utils 文档

## 7. 下一步建议
- 补审 `write_queue/sinks/*.py` 各 sink 的错误处理；统一错误上抛；死信/积压接入用户面告警。
