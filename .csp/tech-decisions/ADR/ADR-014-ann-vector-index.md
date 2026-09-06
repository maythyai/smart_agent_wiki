# ADR-014: ANN 向量索引选型 — hnswlib + numpy 批量矩阵乘 cosine 改进

## 状态：Accepted

## 上下文

v1.13.0 真实 vLLM benchmark 暴露 semantic 检索的可扩展性问题（retrospective-v1.13.0.md finding R2）：

1. **全量 cosine O(n) 线性扫描**：`QueryEngine._semantic_search`（`src/saw/engines/query/engine.py` `_semantic_search` 方法）每次查询执行 `SELECT doc_id, vector, dim FROM embedding_store WHERE workspace_id = ?` 全量拉取所有向量，然后 for 循环 `struct.unpack` + `cosine_similarity` 逐条计算——O(n) 线性增长。v1.13.0 benchmark 在 ≤15 文档规模下 P99=97.82ms，文档数增大时延迟线性退化，不可扩展。

2. **纯 Python cosine 无向量化**：`cosine_similarity`（`src/saw/adapters/embeddings.py` `cosine_similarity` 函数）用 `sum(x * y for x, y in zip(a, b))` + `math.sqrt(...)` 逐元素计算——纯 Python dot product，无 numpy 批量矩阵乘优化。

3. **related_pages 同样 O(n)**：`compute_related_pages`（`src/saw/engines/query/related_pages.py` `compute_related_pages` 函数）对每个候选页面执行 `SELECT vector, dim FROM embedding_store WHERE doc_id = ? AND workspace_id = ?` + `struct.unpack` + `cosine_similarity`——per-page O(1) 但 total O(n) per source page，且重复实现 cosine 扫描。

4. **embedding_store 无向量索引**：`_create_embedding_store`（`src/saw/db/migrations.py` v10 migration）定义 `vector BLOB NOT NULL`，仅有 `idx_embedding_workspace` + `idx_embedding_model` 标量索引——无 ANN/向量索引。

PRD-semantic-perf-v1.14.0 §3.2 要求：向量检索从全量 cosine O(n) 改为 ANN（近似最近邻）索引，大规模时自动切换 ANN 路径，小规模保持 cosine。ANN 库选型约束：须纯 Python 或轻量 C 扩展（pip 可装），MIT/Apache 许可；**不引入 faiss（重依赖）/ torch（重依赖）**。

### CMS 出处（ground 自源码）

| 事实 | file:line | 现状 |
|---|---|---|
| _semantic_search 全量 SELECT + for-cosine | `src/saw/engines/query/engine.py` `_semantic_search` 方法 | `SELECT doc_id, vector, dim FROM embedding_store WHERE workspace_id = ?` → `for doc_id, blob, dim in rows:` → `struct.unpack` → `cosine_similarity` 逐条 |
| _semantic_search cache.get/set 无条件执行 | `src/saw/engines/query/engine.py` `_semantic_search` 方法 | `_cache.get(question, _cache_params)` / `_cache.set(question, _cache_params, _qr)` — 无 env 判断，无阈值跳过 |
| cosine_similarity 纯 Python dot product | `src/saw/adapters/embeddings.py` `cosine_similarity` 函数 | `dot = sum(x * y for x, y in zip(a, b))` + `math.sqrt(...)` — 无 numpy 向量化 |
| embedding_store 无向量索引 | `src/saw/db/migrations.py` v10 `_create_embedding_store` | `vector BLOB NOT NULL`，仅 `idx_embedding_workspace` + `idx_embedding_model` 标量索引 |
| related_pages 全量 cosine 扫描 | `src/saw/engines/query/related_pages.py` `compute_related_pages` 函数 | 对每个候选页面 `SELECT vector, dim FROM embedding_store WHERE doc_id = ? AND workspace_id = ?` → `struct.unpack` → `cosine_similarity` — O(n) per source page |
| cache stats 有 hits 计数 | `src/saw/engines/query/cache.py` `stats` 方法 | `stats()` 返回 `{"hits": self._hits, "misses": self._misses, "size": ..., "hit_rate_percent": ...}` |
| EmbeddingSettings env 读取范式 | `src/saw/config/settings.py` `EmbeddingSettings` + `_api_embedding_configured` | `os.environ.get("SAW_EMBEDDING_MODEL")` / `EMBEDDING_API_KEY` / `SAW_EMBEDDING_API_BASE` — env 驱动配置范式 |
| benchmark _semantic_search 独立函数 | `scripts/benchmark_semantic.py` `_semantic_search` 函数 | 独立函数，直接 `embed_texts()` + cosine，不 import `get_cache`，不经过 QueryEngine cache 路径 |
| benchmark cache 命中用 50% 延迟阈值 | `scripts/benchmark_semantic.py` `_measure_cache_hit` 函数 | `"hit": lat2 < lat1 * 0.5` — 延迟比较阈值，非生产 cache 行为 |

## 决策

### 决策一：ANN 库选型 → 候选 ① hnswlib（pure python pip, MIT, HNSW 算法）

选择候选 ①：**hnswlib**（`pip install hnswlib`，MIT 许可，pure Python binding to C++ HNSW 库）。

- 持久化 `.bin` 索引文件，存储于 `.saw/ann_index_<workspace_id>.bin`，rebuild-embeddings 时构建。
- O(log n) HNSW 近似最近邻检索，大规模（≥1k 文档）时显著优于 O(n) cosine 扫描。
- 无需 faiss/torch 依赖；`hnswlib` wheel 纯 pip 安装，C++ 编译已预构建。
- 降级兜底：hnswlib 未装或索引损坏 → 全量 cosine（`meta.ann_fallback: true`），不报错不中断。

### 决策二：cosine 改进 → 候选 ③ numpy 批量矩阵乘（小规模/fallback 路径）

选择候选 ③：**numpy 批量矩阵乘**改进小规模/fallback 路径的 cosine 计算。

- 将 `cosine_similarity` 逐条 dot product 改为 numpy 矩阵乘（`query_vec @ matrix.T`），一次批量计算所有向量的 cosine。
- 小规模（≤ 阈值）路径和 ANN 降级 fallback 路径均受益——无需逐条 Python 循环。
- numpy 已是既有依赖（ADR-010 引入），无新依赖。
- 不替代 ANN 路径——ANN 处理大规模，numpy 批量矩阵乘优化小规模/fallback。

### 决策三：规模阈值 → SAW_ANN_THRESHOLD 默认 500 [TBD]

- 环境变量 `SAW_ANN_THRESHOLD`：整数，默认 `500`——当 `embedding_store` 行数超过此阈值时自动切换 ANN 路径；低于阈值保持 numpy 批量 cosine。
- 默认值 500 是初步估算 [TBD]——须 05 实施后 benchmark 实测确定 cosine 可接受延迟的拐点（P99 目标 [TBD]）。
- 阈值可配（env），适配不同部署规模。

### 不实现 localhost 自适应

PRD §3.1 业务规则 4 标注的可选自适应（`SAW_EMBEDDING_API_BASE` 含 localhost 时自动禁用 cache）——**不实现**。理由：
1. 语义混乱风险高（localhost 判定逻辑可能误判远程 endpoint 的 hostname）。
2. 用户可通过 `SAW_SEMANTIC_CACHE_ENABLED=false` 显式控制，更明确。
3. 约束原则：显式配置 > 隐式推断。

## 备选方案

### 决策一备选（ANN 库）

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① hnswlib（选） | pure python pip（`pip install hnswlib`），MIT 许可；HNSW 算法 O(log n) 检索；持久化 `.bin` 索引；轻量 C 扩展（无 torch/faiss）；空间效率高（HNSW 图结构紧凑）；pip wheel 预编译无需本地编译 | 需额外 pip 依赖（非 stdlib）；C 扩展须平台 wheel 可用（PyPI 覆盖主流平台）；近似检索（非精确，召回率 ≥95% [TBD]） | 大规模 ANN 检索 ✓ |
| ② sqlite-vss | 与 SQLite 生态融合；无额外进程；SQL 查询向量 | loadable extension 机制（须编译/加载 `.so`/`.dll`）；Python 3.13/3.14 兼容性风险（CPython ABI 变更可能破坏 loadable ext）；社区维护活跃度不如 hnswlib；安装复杂度高于 `pip install` | SQLite 深度集成场景（淘汰：Py3.14 兼容风险 + loadable ext 安装复杂度） |
| ③ numpy 分块矩阵乘（选为 cosine 改进） | 无新依赖（numpy 已有）；批量矩阵乘 O(n) 但常数小（numpy C 内核）；适合小规模（≤500） | 仍 O(n) 线性扫描，大规模不可扩展；无索引结构 | 小规模/fallback 路径 ✓（不替代 ANN） |
| ④ faiss | 业界标准 ANN 库；算法丰富（IVF/HNSW/IVF-PQ）；高性能 | 重依赖（`pip install faiss-cpu` ~50MB，含 C++ 编译）；可能拉入不必要的依赖；与"不引重依赖"约束冲突 | 排除：重依赖，违反 PRD 约束 |

### 决策二备选（cosine 改进）

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| ① 保持纯 Python 逐条 dot product | 无改动 | O(n) 逐条 Python 循环，常数大；大规模时瓶颈 | 不推荐（不改无法提升小规模路径） |
| ③ numpy 批量矩阵乘（选） | 无新依赖；C 内核矩阵乘常数远小于 Python 循环；一次计算所有向量 | 仍 O(n) 线性，但常数大幅降低 | 小规模/fallback ✓ |
| ④ scipy.spatial.distance.cdist | 向量化距离计算 | scipy 是重依赖（非既有）；cosine 须从 distance 转换 | 排除：scipy 重依赖 |

## 理由

### 决策一理由（hnswlib）

1. **约束优先**：PRD §3.2 硬约束"不引入 faiss（重依赖）/ torch（重依赖）"。hnswlib 是纯 pip 安装（`pip install hnswlib`），MIT 许可，C++ 扩展但 wheel 预编译——无 faiss/torch 重量级依赖。
2. **HNSW 算法成熟**：HNSW（Hierarchical Navigable Small World）是业界验证的 ANN 算法，O(log n) 检索复杂度，在高维向量空间表现稳定。hnswlib 是 HNSW 的主流 Python 实现。
3. **持久化 `.bin` 索引**：hnswlib 支持 `save_index(path)` / `load_index(path)`，索引持久化到 `.saw/ann_index_<ws>.bin` 文件，rebuild-embeddings 时构建，查询时加载——无需每次重建。
4. **降级兜底安全**：hnswlib 未安装时（`ImportError`）自动降级到 numpy 批量 cosine，`meta.ann_fallback: true`，不报错不中断——与既有 BM25 fallback 范式一致。
5. **候选 ② sqlite-vss 淘汰理由**：loadable extension 机制（须编译/加载 `.so`/`.dll`）+ Python 3.13/3.14 CPython ABI 变更可能导致 loadable ext 不兼容——违反"轻量 + 可维护"原则。
6. **候选 ④ faiss 排除理由**：`faiss-cpu` 包约 50MB+，含大量 C++ 编译产物，与 PRD §4"不引入重依赖"约束直接冲突。

### 决策二理由（numpy 批量矩阵乘）

1. **零新依赖**：numpy 是既有依赖（ADR-010 引入用于 embedding 处理），无新增。
2. **常数优化显著**：numpy 矩阵乘（`query_vec @ matrix.T`）在 C 内核执行，常数远小于 Python `for` 循环逐条 `sum(x * y for x, y in zip(a, b))`。小规模（≤500）路径 P99 可从 ~97ms 降至 [TBD]。
3. **不替代 ANN**：numpy 批量矩阵乘仍是 O(n) 线性，但常数小——适合小规模（≤ 阈值）和 ANN 降级 fallback 路径。大规模（> 阈值）走 hnswlib ANN。
4. **改动集中**：`cosine_similarity` 函数内加 numpy 批量路径，调用方无需改动（返回值结构不变）。

### 决策三理由（SAW_ANN_THRESHOLD 默认 500）

1. **500 是初步估算**：v1.13.0 benchmark 在 ≤15 文档 P99=97.82ms。假设线性增长，500 文档时 cosine P99 约 ~3000ms+（不可接受），ANN 应在此规模前切入。实际拐点须 05 实施 benchmark 实测确定 [TBD]。
2. **可配**：env 驱动，用户可根据自身硬件/规模调整。

## 后果

### 正面
- 大规模（≥500 文档）semantic 检索走 ANN 路径，O(log n) 不退化。
- 小规模/fallback 路径 cosine 计算常数优化（numpy 批量矩阵乘）。
- 降级兜底安全（hnswlib 未装 → cosine fallback，`ann_fallback: true`）。
- `related_pages.py` 复用 ANN 路径，消除重复 cosine 扫描实现。

### 负面
- 新增 `hnswlib` pip 依赖（轻量，MIT，但非 stdlib）——`pyproject.toml` `[optional-dependencies]` 或 `[semantic]` extra 声明。
- ANN 索引文件 `.saw/ann_index_<ws>.bin` 须随 rebuild-embeddings 构建/重建——增加 rebuild 耗时。
- ANN 是近似检索，召回率 ≥95% [TBD]——须 benchmark 验证。
- numpy 批量矩阵乘改动触及 `cosine_similarity` 公共函数——须回归测试。

### 风险
- hnswlib wheel 在冷门平台（如 Alpine musl）不可用 → 降级 cosine fallback（`ann_fallback: true`），不影响功能。
- ANN 召回率不足 → 设 ≥95% 验收门槛；不达标时降级 cosine [TBD]。
- ANN 索引与 embedding_store 增量同步 → rebuild-embeddings 全量重建索引；写入时标记 dirty 须后续增量更新 [TBD]。

## 关联 Feature

- F-S-1（semantic cache 阈值可配——cache 路径 env 控制，本 ADR 不直接涉及但同属 v1.14.0 技术方案）
- F-S-2（ANN 索引替代全量 cosine——本 ADR 核心决策）
- F-S-3（benchmark 更新——ANN vs cosine 对比依赖本 ADR 的 ANN 路径）

## 关联 ADR

- ADR-010（embedding_store BLOB + numpy cosine 存储/检索，Accepted）——ANN 索引为附加结构，不改 embedding_store 表结构。
- ADR-011（semantic search cache，Accepted）——cache 路径不变，ANN 切换在 cache 之后的检索阶段。
- ADR-012（embedding provider litellm API，Accepted）——embed_texts() API 路径不变，ANN 索引消费 embedding_store 中的向量。
- ADR-013（ingest 递归 + benchmark 方法论，Accepted）——benchmark 脚本复用既有方法论，更新 cache 度量 + ANN 对比。

## [TBD] 留尾

- `SAW_ANN_THRESHOLD` 默认值 500 须 05 实施后 benchmark 实测确定 cosine 可接受延迟拐点。
- ANN 召回率 ≥95% 精度指标须 05 实施后 benchmark 验证。
- ANN P99 < cosine P99 @ ≥1k 文档的目标值须 benchmark 跑完填实际值。
- ANN 索引增量更新策略（写入时增量 vs 全量重建）须 05 实施时确定。
