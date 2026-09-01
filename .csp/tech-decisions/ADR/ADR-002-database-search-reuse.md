# ADR-002: 数据库与搜索复用（SQLite + FTS5 + Write Queue outbox）

## 状态：Accepted
## 上下文
SAW 四层存储（Vault→Claims→Wiki→Index）基于单 SQLite 库 `saw.db`，FTS5 做 BM25 检索（`fts5_utils.py`/`fts_tokenize.py`），Write Queue（SQLite outbox + Dispatcher + sinks）为唯一变更网关（CMS §M09）。硬化不涉及存储迁移。
## 决策
复用 SQLite + FTS5 + Write Queue。不引入 Postgres/Elasticsearch/Redis。冒烟/限流用既有 SQLite（限流计数可进程内或 SQLite，F-C-3 复用 `rate_limit.py`）。
## 备选方案
| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| SQLite + FTS5（复用） | local-first 零运维，单文件可移植 | 并发写单写锁 | 单机/小团队 ✓ |
| Postgres + pgvector | 并发/事务/GIS | 需服务进程，破 local-first | 多用户高并发 |
| Elasticsearch | 全文更强 | 重运维，资源大 | 大规模检索 |
## 理由
需求匹配（local-first + 单文件 + 四层存储已建）40% + 团队能力 20% + 生态 15% + 运维（零外部服务）15% + 成本（零）10%。Write Queue outbox 已保证 mutation 不丢。
## 后果
- 正：零迁移，冒烟可在 fresh 库从 0 起跑；outbox 保障可靠。
- 负：高并发写受限（非本项目场景）。
- 风险：单库备份策略 [TBD]（F-E/可观测无关，归运维）。
## 关联 Feature
F-A-1（fresh 库）、F-A-2（ingest→compile）、F-A-3（FTS5 检索）、F-C-2（write_queue 变更挂 receipt）、F-C-3（限流）
