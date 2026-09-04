# ADR-010: Embedding 向量存储与检索融合策略

## 状态：Accepted

## 上下文

v1.10.0 embedding 周期（PRD-embedding-v1.10.0）需将 embedding 从 Learn 引擎专用扩展到 Query 引擎检索 + smart-linking。PRD §2.3 非目标明确"不引入外部 DB"，约束在本地 SQLite 生态内实现向量存储。需决策：

1. **向量存储方案**：claim/wiki 页面向量如何持久化（新表 vs 加列 vs 向量扩展）。
2. **BM25+semantic 检索关系**：语义检索与既有 BM25 词面检索如何共存（显式切换 vs 融合排序）。
3. **embedding 模型**：沿用既有 `all-MiniLM-L6-v2` 还是升级。

### CMS 出处（ground 自源码）

| 事实 | file:line | 现状 |
|---|---|---|
| `embed_texts()` 返回 L2-normalized 向量或 None | `src/saw/adapters/embeddings.py:41-57` | 已加载 `all-MiniLM-L6-v2`（384 维），try/except 降级 |
| `cosine_similarity()` 纯 Python dot product | `src/saw/adapters/embeddings.py:60-66` | 可复用，无 numpy 依赖 |
| `embeddings_available()` 检测 sentence_transformers | `src/saw/adapters/embeddings.py:19-29` | 全局缓存 `_ST_available` |
| `detect_tier()` 返回 FULL 当 embeddings 可用 | `src/saw/config/settings.py:115-120` | `_embeddings_available()` 用 importlib 检测 |
| `FTS5Search.search()` 用 `bm25(fts_index)` 排序 | `src/saw/engines/query/search.py:60-69` | 返回 `SearchResult(claim_uuids, contents, scores, total)` |
| `QueryEngine.query()` mode 路由：auto/search/graph/compare/tree | `src/saw/engines/query/engine.py:107-120` | **无 semantic 模式** |
| `QueryEngine.__init__` 接收 `workspace_id` | `src/saw/engines/query/engine.py:58` | workspace 隔离已有 |
| `compute_related_pages()` 3-signal（tags 2.0 / links 3.0 / type 1.0） | `src/saw/engines/query/related_pages.py:35-57` | 无 embedding 信号 |
| `FTS5Sink.write(op)` + `can_handle(sink_name)` 范式 | `src/saw/write_queue/sinks/fts5_sink.py:18-40` | Write Queue sink 可参照 |
| migration v8: claim 表 `workspace_id` 列 | `src/saw/db/migrations.py:283-296` | `workspace_id TEXT NOT NULL DEFAULT 'default'` |
| migration v9: entity 表 `workspace_id` 列 | `src/saw/db/migrations.py:319-325` | 最新 version=9，v10 为下一个 |
| `search_cmd.py` `--mode default|tree` | `src/saw/drivers/cli/commands/search_cmd.py:22` | 增 `semantic` 选项 |
| `main.py` 命令注册 `app.command(name="search")(search)` | `src/saw/drivers/cli/main.py:78` | 独立函数注册 |

## 决策

### 1. 向量存储：新表 `embedding_store` + BLOB 向量 + numpy cosine 内存计算

**选择候选 ①**：新建 `embedding_store` 表，向量以 BLOB（`struct.pack` 序列化 float32 数组）存储，检索时全量载入内存用 `embeddings.py::cosine_similarity()`（或 numpy dot product，L2-normalized 向量 dot = cosine）计算 top-K。

表结构（migration v10）：
```sql
CREATE TABLE IF NOT EXISTS embedding_store (
    doc_id TEXT NOT NULL,          -- claim UUID 或 wiki slug
    entity_type TEXT NOT NULL,     -- 'claim' | 'wiki'
    model TEXT NOT NULL,           -- 'all-MiniLM-L6-v2'
    vector BLOB NOT NULL,          -- struct.pack float32 数组
    dim INTEGER NOT NULL,          -- 384
    workspace_id TEXT NOT NULL DEFAULT 'default',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (doc_id, workspace_id)
);
CREATE INDEX IF NOT EXISTS idx_embedding_workspace
    ON embedding_store(workspace_id);
CREATE INDEX IF NOT EXISTS idx_embedding_model
    ON embedding_store(model);
```

**设计要点**：
- `doc_id` + `workspace_id` 联合主键 → workspace 隔离天然覆盖（参照 ADR-008/009 范式）。
- `model` + `dim` 列 → 维度变更检测：重建时若 `dim != 当前模型 dim` 则全量清除重建。
- 向量 BLOB 序列化：`struct.pack(f"<{dim}f", *vec)` / `struct.unpack(f"<{dim}f", blob)`。
- 检索时 `SELECT doc_id, vector FROM embedding_store WHERE workspace_id=?`，全量载入内存（小库场景），逐条 `cosine_similarity()` 排序取 top-K。

### 2. BM25+semantic 检索关系：用户显式 --mode 切换（并行模式，不融合）

**选择候选 ①**：`saw search --mode semantic` 走纯语义检索，`--mode default` 走纯 BM25，两路径独立。不实现 RRF 融合排序。

**理由**：PRD §3.2 描述 "与既有 BM25 并行/融合"——本轮选并行（最简、低风险），融合留后续升级路径。降级时自动回退到 BM25（meta 标注 `semantic_fallback: true`）。

### 3. Embedding 模型：沿用 `all-MiniLM-L6-v2`（384 维）

**理由**：`embeddings.py::_get_model()` 已加载此模型（`src/saw/adapters/embeddings.py:33-38`），Learn 引擎聚类已在用，切换模型无收益且引入风险（维度变更须全量重建）。384 维 × 4 bytes = 1536 bytes/doc，存储开销低。

## 备选方案

### 向量存储候选对比

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① 新表 `embedding_store` + BLOB + numpy cosine 内存计算（选） | 最轻量，零新依赖，复用既有 `cosine_similarity()`/`embed_texts()`，local-first 契合，workspace 隔离天然覆盖 | 全量载入内存，规模上限受限于文档数（~10K docs × 384 × 4B ≈ 15MB，可接受；[TBD] 精确上限需 benchmark） | 本地 SQLite 生态，小库优先 ✓ |
| ② sqlite-vec 扩展 | 原生 SQL 向量检索，无需全量载入 | 需安装 C 扩展（非纯 Python），违反"不引新依赖"约束倾向，编译环境复杂 | 需编译扩展，不适合 local-first |
| ③ FAISS（MIT，本地） | 业界标准，高性能 ANN 检索 | 重依赖（需 numpy + faiss C++），违反"本地 SQLite 生态"约束，过度工程 | 大规模库（>100K docs），本轮不需要 |

### BM25+semantic 融合候选对比

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① 用户显式 --mode 切换，不融合（选） | 最简实现，零排序复杂度，用户可控，降级路径清晰 | 无法同时利用词面+语义召回 | 本轮 additive MINOR，低风险优先 ✓ |
| ② RRF（Reciprocal Rank Fusion）混合排序 | 同时利用 BM25 精确匹配 + 语义召回，提升整体召回率 | 实现+调参复杂度高，RRF k 常数需调优，测试复杂 | 后续升级路径（v1.11+ candidate） |

## 理由

1. **local-first 契合**：PRD §2.3 明确"不引入外部 DB"。候选 ① 零新依赖，复用既有 `embeddings.py`（cosine_similarity 已有纯 Python 实现）+ SQLite BLOB 存储，与项目六角架构 + SQLite 单库一致。
2. **轻量优于重量**（选型六原则②）：候选 ① 是最轻量方案，满足需求前提下不引 sqlite-vec/FAISS 重依赖。
3. **workspace 隔离**：`embedding_store` 表含 `workspace_id` 列，参照 ADR-008（claim 写入）/ADR-009（entity 隔离）范式，跨 workspace 查询不泄漏。
4. **维度变更安全**：`model` + `dim` 列使重建命令可检测模型变更 → 全量清除重建，避免维度不一致导致 cosine 计算错误。
5. **并行模式低风险**：additive MINOR 版本，不改变既有 BM25 路径行为，semantic 为新增独立路径，降级回退 BM25 保证 tier<FULL 时零感知。

## 后果

### 正面
- embedding 向量持久化在 SQLite 单库，零外部依赖。
- workspace 隔离覆盖（embedding_store.workspace_id）。
- 维度变更检测机制安全。
- 降级策略完备（tier<FULL → BM25）。

### 负面
- 全量载入内存检索，规模上限 [TBD]（预估 ~10K docs 可接受，超出需升级）。
- 纯 Python cosine 计算性能低于 numpy/FAISS（小库场景可接受）。
- 无 BM25+semantic 融合（用户须显式选模式）。

### 风险
- **规模上限 [TBD]**：精确性能边界需 05 实施后 benchmark。预估 10K docs × 384 维 cosine 全量计算在毫秒级可接受。
- **升级路径**：若库增长到超 10K docs，可升级到 sqlite-vec 或 FAISS（不改变 API 契约，只换 embedding_store 读写实现）。

## 规模上限与升级路径

| 阶段 | 文档数 | 向量存储 | 检索方式 | 延迟预估 |
|---|---|---|---|---|
| 本轮（v1.10.0） | < 10K | embedding_store BLOB + 全量内存 cosine | 纯 Python cosine_similarity | [TBD] 毫秒级 |
| 升级候选 A | 10K-100K | sqlite-vec 扩展 | SQL 向量检索 | 需 benchmark |
| 升级候选 B | > 100K | FAISS 索引 | ANN 检索 | 毫秒级 |

> 升级时只换 `embedding_store` 读写层实现，API 契约（`saw search --mode semantic` / `GET /api/v1/search?mode=semantic`）不变。

## 关联 Feature
F-N-1（embedding 索引）、F-N-2（语义检索）、F-N-3（smart-linking embedding 信号）
