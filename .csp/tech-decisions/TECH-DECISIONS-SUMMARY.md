# Tech Decisions Summary — 供下游消费

> 棕地硬化项目，选型 = 复用既有栈 + 4 ADR 留档。无新触发维度需选型。

## 决策清单
| ADR | 维度 | 决策 | 状态 | 关联 Feature |
|---|---|---|---|---|
| ADR-001 | 语言/框架 | Python 3.11 + Typer + FastAPI + FastMCP 复用 | Accepted | A1-6, D1-3, C* |
| ADR-002 | DB/搜索 | SQLite + FTS5 + Write Queue outbox 复用 | Accepted | A1-3, C2, C3 |
| ADR-003 | 可观测 | 自建 JSON log + trace_id middleware 复用 | Accepted | D1-3, E3 |
| ADR-004 | 安全 | JWT/Cedar/Ed25519 receipt/限流/URL guard 复用 | Accepted | C1-5 |
| ADR-010 | 向量存储+检索融合 | 新表 embedding_store + BLOB + numpy cosine 内存计算；--mode 并行不融合；all-MiniLM-L6-v2 384 维 | Accepted | F-N-1, F-N-2, F-N-3 |
| ADR-011 | semantic search cache | 复用 F-QS-07 cache 单例，mode="semantic" key 隔离；TTL 300s；ingest/rebuild clear 失效 | Accepted | F-O-1, F-N-1, F-N-2 |
| ADR-012 | embedding provider | litellm.embedding API 为主 + 本地 ST 可选 fallback；EmbeddingSettings 复用 LLMSettings 范式；API > ST > BM25 三级路由 | Accepted | F-Q-1, F-Q-2, F-Q-3, F-Q-4 |
| ADR-013 | ingest 递归 + benchmark | pipeline 入口递归 + 独立 scripts/benchmark_semantic.py 真实 vLLM | Accepted | F-R-1, F-R-2 |
| ADR-014 | ANN 向量索引 | hnswlib（HNSW, MIT, pip）+ numpy 批量矩阵乘 cosine 改进；SAW_ANN_THRESHOLD 默认 500 [TBD]；不引 faiss/torch；不实现 localhost 自适应 | Accepted | F-S-1, F-S-2, F-S-3 |
| ADR-015 | agent 角色注册+活动聚合 | YAML 配置文件 + build_default_agents 合并（候选①>②DB表）；event_bus subscriber 写内存计数器（候选①>②DB聚合）；复用 BaseAgent/InMemoryEventBus/WikiRepository；不持久化 | Accepted | F-T-1, F-T-2, F-T-3 |
| ADR-016 | realtime 仪表盘更新策略 | react-query refetchInterval polling 15s + 复用既有 WebSocket（候选②>①SSE>③纯WS）；无新后端端点；useWebSocket 已有 invalidateQueries；polling interval 15s（≥10s 下限） | Accepted | F-U-1, F-U-2, F-U-3 |
| ADR-017 | desktop 嵌入策略 + 端口收敛 | Hybrid（dev proxy + prod external，sidecar defer）；vite proxy 8080→8000 收敛；CORS 添加 localhost:5173；prod external saw web + VITE_API_BASE_URL 配置；sidecar defer v2.0 候选（候选③>①sidecar>②external-only） | Accepted | F-V-1, F-V-2, F-V-3, F-V-4 |

## 复用原则
- 全栈既有（六角架构/write_queue/observability/RBAC/receipt/FTS5），硬化只补"有模块→全链路闭环"。
- 每处设计 reference CMS 入口点（标注"源自 CMS"），不重复 spec 已有 schema/API。

## 选型门控
- [x] 触发维度全覆盖（needs_database/queue/ai/realtime/search/file_storage 全由既有承载）
- [x] ADR ≥3（6 份）
- [x] 一致性（无新框架冲突）
- [x] NFR 匹配

## [TBD] 留尾
- 覆盖率基线（F-E-1 实测后定阈值）
- 前端 token 互通（F-C-5 实机核验）
- receipt 覆盖率（F-C-2 核验）
- 备份/SLA/告警通道（运维 [TBD]，非本硬化范围）
