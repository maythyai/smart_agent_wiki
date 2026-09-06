---
id: SPEC-F-S-2
title: ANN 索引替代全量 cosine 扫描（规模驱动自动切换 + cosine 降级兜底）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-06"
prd_ref: docs/prd/PRD-semantic-perf-v1.14.0.md
pms_ref: .csp/product-spec/PMS-semantic-perf.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-S-2
complexity: L
tdd_ref: .csp/tech-decisions/ADR/ADR-014-ann-vector-index.md
adr_ref: .csp/tech-decisions/ADR/ADR-014-ann-vector-index.md
ac_coverage: 5/5
related_tasks: [".csp/tasks/TASKS-DELTA-v1.14.0.md (T-F-S-2)"]
---

# SPEC-F-S-2: ANN 索引替代全量 cosine 扫描

## 实现 delta（ground 自源码）

> ADR-014 决策：hnswlib（ANN 索引）+ numpy 批量矩阵乘（cosine 改进）。
> embedding_store 表结构不变（向量仍 BLOB 存储），ANN 索引为附加 `.bin` 文件。

### 改动点

| 文件 | 现状（ground） | 改为 |
|---|---|---|
| `src/saw/engines/query/engine.py` `_semantic_search` 方法 | `SELECT doc_id, vector, dim FROM embedding_store WHERE workspace_id = ?` → `for doc_id, blob, dim in rows:` → `struct.unpack` → `cosine_similarity` 逐条——O(n) 线性 | 规模驱动切 ANN：`embedding_store` 行数 > `SAW_ANN_THRESHOLD` → hnswlib ANN 索引检索 top-K；≤ 阈值 → numpy 批量矩阵乘 cosine；ANN 失败 → numpy cosine fallback + `meta.ann_fallback: true` |
| `src/saw/adapters/embeddings.py` `cosine_similarity` 函数 | `sum(x * y for x, y in zip(a, b))` + `math.sqrt(...)`——纯 Python 逐元素 | 新增 `batch_cosine_similarity(query_vec, matrix)` 函数：numpy 矩阵乘（`query_vec @ matrix.T`）一次批量计算——小规模/fallback 路径使用 |
| `src/saw/engines/query/related_pages.py` `compute_related_pages` 函数 | 对每个候选页面 `SELECT vector, dim FROM embedding_store WHERE doc_id = ? AND workspace_id = ?` → `struct.unpack` → `cosine_similarity`——O(n) per source page | 复用 ANN 路径（规模 > 阈值时走 hnswlib，≤ 阈值走 numpy 批量 cosine），不重复实现 cosine 扫描 |
| `pyproject.toml` | 无 hnswlib 依赖 | 新增 `hnswlib` 到 `[semantic]` extra（`pip install smart_agent_wiki[semantic]`）或 optional-dependencies |

### 不改动

- `src/saw/db/migrations.py`——`embedding_store` 表结构不变（`vector BLOB NOT NULL`，PK `(doc_id, workspace_id)`，`idx_embedding_workspace` + `idx_embedding_model` 标量索引）。ANN 索引为附加 `.bin` 文件，不在 DB 中。
- `embed_texts()` / `embeddings_available()`——provider 接口不变（v1.12.0 litellm API，ADR-012）。
- `QueryResult` 返回值结构——`meta` 新增 `ann_fallback` / `ann_search` 标记，但 `QueryResult` 字段不变。
- `QueryCache`——cache 路径不受 ANN 切换影响（cache 在检索之前/之后，ANN 是检索路径内部的优化）。

## 后端架构

### ANN 索引结构

```
.saw/
  ann_index_<workspace_id>.bin    # hnswlib 持久化索引文件
```

- **构建时机**：`rebuild-embeddings` 命令执行时，全量从 `embedding_store` 加载所有向量 → 构建 hnswlib 索引 → `save_index(path)` 持久化。
- **加载时机**：`_semantic_search` 首次访问时 `load_index(path)`（lazy load，缓存在内存）。
- **增量更新**：embedding_store 写入新向量时，标记索引 dirty [TBD]——05 实施时决定是增量更新还是下次 rebuild 全量重建。
- **workspace 隔离**：每个 workspace_id 独立索引文件（`ann_index_<ws>.bin`），参照既有 `embedding_store` PK `(doc_id, workspace_id)` 隔离范式。

### 规模驱动切 ANN（`engine.py` `_semantic_search`）

```python
# 伪代码

import os

def _semantic_search(self, question, limit=20, offset=0):
    # ... cache 路径（F-S-1 条件分支）...

    # 规模检测
    doc_count = self._conn.execute(
        "SELECT COUNT(*) FROM embedding_store WHERE workspace_id = ?",
        (self._workspace_id,)
    ).fetchone()[0]

    ann_threshold = int(os.environ.get("SAW_ANN_THRESHOLD", "500"))

    if doc_count > ann_threshold:
        # 走 ANN 路径
        try:
            results = self._ann_search(query_vec, limit, offset)
            results.meta["ann_search"] = True
            return results
        except (ImportError, Exception) as e:
            logger.warning("ANN search failed, falling back to cosine: %s", e)
            # 降级 cosine
            results = self._cosine_search_batch(query_vec, limit, offset)
            results.meta["ann_fallback"] = True
            return results
    else:
        # 小规模走 numpy 批量 cosine
        results = self._cosine_search_batch(query_vec, limit, offset)
        return results
```

### numpy 批量 cosine（`embeddings.py`）

```python
def batch_cosine_similarity(
    query_vec: list[float], matrix: list[list[float]]
) -> list[float]:
    """Batch cosine similarity via numpy matrix multiply.

    Args:
        query_vec: Query embedding vector (1D).
        matrix: All document embedding vectors (2D, rows=docs).

    Returns:
        List of cosine similarity scores (one per document).
    """
    import numpy as np

    q = np.array(query_vec, dtype=np.float32)
    m = np.array(matrix, dtype=np.float32)
    # L2 normalize
    q_norm = q / (np.linalg.norm(q) + 1e-12)
    m_norm = m / (np.linalg.norm(m, axis=1, keepdims=True) + 1e-12)
    # Batch cosine via matrix multiply
    return (m_norm @ q_norm).tolist()
```

### ANN 检索（hnswlib）

```python
def _ann_search(self, query_vec, limit, offset):
    """ANN search via hnswlib index."""
    import hnswlib

    index_path = f".saw/ann_index_{self._workspace_id}.bin"
    # Lazy load index
    if self._ann_index is None:
        self._ann_index = hnswlib.Index(
            space='cosine', dim=len(query_vec)
        )
        self._ann_index.load_index(index_path)

    # Query top-K + offset
    labels, distances = self._ann_index.knn_query(
        query_vec, k=offset + limit
    )
    # 取 offset:offset+limit
    top_k = labels[offset:offset + limit]
    # labels 是 doc_id（构建时存入）
    # distances 是 cosine distance（1 - cosine_similarity）
    ...
```

### related_pages 复用 ANN 路径

```python
# related_pages.py compute_related_pages 改动

# 既有：for page_slug in wiki_repo.list_pages():
#           SELECT vector, dim FROM embedding_store WHERE doc_id = ? AND workspace_id = ?
#           struct.unpack + cosine_similarity 逐条

# 改为：规模 > 阈值时，复用 ANN 索引检索 top-K 相关页面
#       ≤ 阈值时，numpy 批量 cosine（一次加载所有向量）
```

## 数据库 Schema

无 schema 变更。`embedding_store` 表结构不变（`vector BLOB NOT NULL`，PK `(doc_id, workspace_id)`）。ANN 索引为附加 `.bin` 文件。

## API 契约

无 API 变更。`QueryEngine._semantic_search` 是内部方法，返回 `QueryResult` 不变。`meta` 新增可选字段：
- `meta.ann_search: true`——ANN 路径执行（大规模）
- `meta.ann_fallback: true`——ANN 失败降级 cosine

## 测试策略（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-B-1（ANN 自动切换） | `tests/unit/test_ann_search.py`（新建）：mock embedding_store 行数 > `SAW_ANN_THRESHOLD` → semantic 查询 → `meta` 含 `ann_search: true`，不含 `ann_fallback` | `meta.ann_search == True` |
| AC-B-2（小规模 cosine） | `test_ann_search.py`：mock embedding_store 行数 ≤ `SAW_ANN_THRESHOLD` → semantic 查询 → `meta` 不含 ANN 标记 | `meta` 无 `ann_search` / `ann_fallback` |
| AC-B-3（ANN 降级） | `test_ann_search.py`：mock hnswlib `ImportError` 或索引损坏 → semantic 查询 → 降级 cosine，`meta.ann_fallback: true`，不报错 | `meta.ann_fallback == True`，无异常抛出 |
| AC-B-4（召回一致性） | `test_ann_search.py`（标 marker，CI 可跑）：构建小数据集，ANN 路径 vs cosine 路径 top-K 重叠率 ≥95% [TBD] | overlap_ratio >= 0.95 |
| AC-B-5（related_pages 复用） | `tests/unit/test_related_pages_ann.py`（新建或扩）：mock 规模 > 阈值 → `compute_related_pages` → 走 ANN 路径，不逐条 SELECT + cosine | 不执行逐条 SELECT，走批量路径 |

**CI 兼容**：AC-B-1/2/3/5 用 mock（不依赖 vLLM），CI 始终跑。AC-B-4 召回率验证可 mock 小数据集。hnswlib 须 `pip install hnswlib`（CI 装 `[semantic]` extra）；未装时 ANN 测试标记 skip，cosine 路径测试仍跑。

## 安全考量

- ANN 库 hnswlib MIT 许可（符合约束）。
- 不引入 faiss/torch 重依赖。
- 向量数据不含额外 PII（embedding 输入为 claim/wiki 内容文本，非用户数据）。
- workspace_id 隔离：ANN 索引文件按 workspace 分离（`ann_index_<ws>.bin`）。

## 实现就绪度

- [x] ANN 库选型定（hnswlib，ADR-014）
- [x] 规模阈值定（`SAW_ANN_THRESHOLD` 默认 500 [TBD]）
- [x] 切换逻辑定（规模 > 阈值 → ANN；≤ 阈值 → numpy cosine；ANN 失败 → cosine fallback）
- [x] 降级兜底定（`meta.ann_fallback: true`，不报错不中断）
- [x] numpy 批量 cosine 函数定（`batch_cosine_similarity`）
- [x] related_pages 复用 ANN 路径定
- [x] embedding_store 表结构不变
- [x] AC 覆盖 5/5
- [ ] `SAW_ANN_THRESHOLD` 默认值 500 须 benchmark 实测确认 [TBD]
- [ ] ANN 召回率 ≥95% 须 benchmark 验证 [TBD]
- [ ] ANN 索引增量更新策略 05 实施时确定 [TBD]
