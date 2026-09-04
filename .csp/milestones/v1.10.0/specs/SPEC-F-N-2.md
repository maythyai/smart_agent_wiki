---
id: SPEC-F-N-2
title: 语义检索端点+CLI（QueryEngine semantic 模式 + saw search --mode semantic + REST）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-04"
prd_ref: docs/prd/PRD-embedding-v1.10.0.md
pms_ref: .csp/product-spec/PMS-embedding.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-N-2
complexity: M
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
adr_ref: .csp/tech-decisions/ADR/ADR-010-embedding-storage-retrieval.md
ac_coverage: 3/3
related_tasks: [T-F-N-2]
---

# SPEC-F-N-2: 语义检索端点 + CLI

## 实现 delta（ground 自源码）

- **QueryEngine.query()** 增 `mode=semantic`（`src/saw/engines/query/engine.py:107-120`）：新增 `_semantic_search()` 分支，与 `_keyword_search`(194) / `_graph_query`(277) / `_compare_query`(333) / `_tree_query`(392) 并行。
- **CLI search_cmd.py** `--mode` 枚举增 `semantic`（`src/saw/drivers/cli/commands/search_cmd.py:22`，现有 `default|tree` → `default|tree|semantic`）。
- **REST** `GET /api/v1/search?mode=semantic`（增参数值，既有端点在 `api/routes/query_ingest_learn.py` 或 `drivers/web/routes/search.py`）。
- **复用** `embeddings.py::embed_texts()`（查询文本 embedding）+ `cosine_similarity()`（相似度计算）+ `detect_tier()`（降级检测）。
- **复用** `FTS5Search.search()`（降级路径）。

## 后端架构

### QueryEngine._semantic_search()（新增分支）

```python
def _semantic_search(self, question: str, limit: int = 20) -> QueryResult:
    """Semantic search via embedding cosine similarity.

    Returns top-K results ranked by cosine similarity to the query
    embedding. Falls back to BM25 when embeddings unavailable or
    index empty.
    """
    # 1. Tier check: degrade to BM25 if embeddings unavailable
    from saw.adapters.embeddings import embeddings_available, embed_texts, cosine_similarity
    if not embeddings_available():
        result = self._keyword_search(question, limit=limit)
        result.mode = "semantic_fallback"
        result.meta = {**(result.meta or {}), "semantic_fallback": True}
        return result

    # 2. Embed query text
    vecs = embed_texts([question])
    if vecs is None:
        # Embedding failed (model error) → degrade to BM25
        result = self._keyword_search(question, limit=limit)
        result.mode = "semantic_fallback"
        result.meta = {**(result.meta or {}), "semantic_fallback": True, "embedding_error": True}
        return result
    query_vec = vecs[0]

    # 3. Load all vectors for this workspace from embedding_store
    import struct
    rows = self._conn.execute(
        "SELECT doc_id, vector, dim FROM embedding_store WHERE workspace_id = ?",
        (self._workspace_id,),
    ).fetchall()

    if not rows:
        # Empty index → return empty result with hint
        return QueryResult(
            answer="embedding index empty, use BM25 mode",
            mode="semantic",
            meta={"semantic_fallback": False, "index_empty": True},
        )

    # 4. Compute cosine similarity for each, sort descending, take top-K
    scored = []
    for doc_id, blob, dim in rows:
        vec = list(struct.unpack(f"<{dim}f", blob))
        sim = cosine_similarity(query_vec, vec)
        scored.append((doc_id, sim))
    scored.sort(key=lambda x: -x[1])
    top_k = scored[:limit]

    # 5. Resolve doc_id → claim/wiki content (reuse _keyword_search resolution)
    sources = []
    for doc_id, sim in top_k:
        claim = self._claims_repo.get_by_id(doc_id, workspace_id=self._workspace_id)
        if claim:
            sources.append({
                "claim_uuid": doc_id,
                "content": claim.content,
                "score": sim,
                "type": "claim",
                "tags": list(claim.tags or []),
            })
        else:
            page = self._wiki_repo.read(doc_id) if self._wiki_repo else None
            if page:
                sources.append({
                    "page_slug": doc_id,
                    "title": page.title,
                    "content": page.content,
                    "score": sim,
                    "type": page.entity_type,
                    "tags": list(getattr(page, "tags", []) or []),
                })

    return QueryResult(
        answer=f"Found {len(sources)} semantic results for '{question}':\n"
              + "\n".join(f"{i+1}. {s.get('content','')[:80]}... (score: {s['score']:.3f})"
                           for i, s in enumerate(sources)),
        sources=sources,
        coverage=100.0,
        mode="semantic",
        meta={"total": len(sources), "limit": limit, "semantic_fallback": False},
    )
```

### QueryEngine.query() mode 路由扩展

在 `engine.py:107-120` 的 `query()` 方法中，在 `elif mode == "tree":` 之前追加：

```python
elif mode == "semantic":
    return self._semantic_search(question, limit=limit, offset=offset)
```

### CLI search_cmd.py 修改

`src/saw/drivers/cli/commands/search_cmd.py:22`：
- `--mode` 帮助文本改为 `"Search mode: default|tree|semantic"`
- 新增 `semantic` 分支：

```python
if mode == "semantic":
    # Use QueryEngine with semantic mode
    from saw.engines.query.engine import QueryEngine
    # ... initialize QueryEngine (reuse existing init pattern)
    result = engine.query(keywords, mode="semantic", limit=limit)
    _display_semantic_results(result, keywords, search_time)
elif mode == "tree":
    # existing tree mode
```

> **注意**：当前 `search_cmd.py` 是独立函数（非 Typer app），直接用 `FTS5Search`。semantic 模式需要 `QueryEngine` 实例（含 claims_repo/wiki_repo/conn/workspace_id）。因此 search_cmd 须在 `mode == "semantic"` 时初始化 QueryEngine（参照 `query_cmd.py` 的初始化模式）。

### REST API 契约（OpenAPI 级）

**端点**：`GET /api/v1/search`

**参数**：
| 参数 | 类型 | 默认 | 枚举 | 说明 |
|---|---|---|---|---|
| q | string | — | — | 搜索查询文本（必填） |
| mode | string | default | default\|tree\|semantic | 搜索模式 |
| limit | int | 10 | 1-100 | 最大结果数 |
| offset | int | 0 | 0+ | 分页偏移 |

**响应 200**（mode=semantic, tier=FULL）：
```json
{
  "results": [
    {
      "doc_id": "claim-uuid-or-wiki-slug",
      "content": "...",
      "score": 0.847,
      "type": "claim",
      "tags": ["python", "ml"]
    }
  ],
  "total": 5,
  "mode": "semantic",
  "meta": {
    "semantic_fallback": false,
    "index_empty": false
  }
}
```

**响应 200**（mode=semantic, tier=LIGHTWEIGHT → 降级 BM25）：
```json
{
  "results": [...],
  "total": 3,
  "mode": "semantic_fallback",
  "meta": {
    "semantic_fallback": true
  }
}
```

**响应 200**（mode=semantic, 索引为空）：
```json
{
  "results": [],
  "total": 0,
  "mode": "semantic",
  "meta": {
    "semantic_fallback": false,
    "index_empty": true
  }
}
```

**错误**：不返回 500（降级到 BM25），不返回 404（空索引返回空结果）。仅在 query 参数缺失时返回 400。

## 降级策略

| 条件 | 行为 | meta 标注 |
|---|---|---|
| tier=FULL + 索引非空 | 纯语义检索，cosine 相似度 top-K | `semantic_fallback: false` |
| tier=LIGHTWEIGHT/OFFLINE | 降级到 BM25 + `semantic_fallback: true` | `semantic_fallback: true` |
| tier=FULL + 索引为空 | 返回空结果 + 提示 | `index_empty: true` |
| tier=FULL + embed 失败（模型异常） | 降级到 BM25 + `embedding_error` | `semantic_fallback: true, embedding_error: true` |

## 安全考量

- **workspace 隔离**：`_semantic_search()` 查询 `WHERE workspace_id = ?`（`self._workspace_id`），跨 workspace 不泄漏。QueryEngine.__init__ 已有 `workspace_id` 参数（`engine.py:58`）。
- **缓存**：语义检索不使用 `_keyword_search` 的缓存路径（`cache.py`），因向量相似度结果时效性依赖索引完整性。可后续加缓存（[TBD]）。

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-SEM-1（语义检索返回同义结果） | `tests/unit/test_semantic_search.py`（新建）：importorskip + seed claim "ML" content → search "machine learning" --mode semantic → 返回含 "ML" 的结果 + score > 0 + mode=semantic + 按相似度降序 | 同义召回 + score 降序 + mode=semantic |
| AC-SEM-2（无 [learn] 降级 BM25） | `tests/unit/test_semantic_search.py`：mock `embeddings_available()=False` → search --mode semantic → 返回 BM25 结果 + meta.semantic_fallback=true + exit 0 | 降级 BM25 + fallback 标注 + 无异常 |
| AC-SEM-3（空索引优雅处理） | `tests/unit/test_semantic_search.py`：空 DB → search --mode semantic → 空结果 + meta.index_empty=true + exit 0 | 空结果 + index_empty 标注 + exit 0 |

## 实现就绪度

- [x] QueryEngine.query() mode 路由可扩展（`engine.py:107-120` 增 elif 分支）
- [x] `embed_texts()` / `cosine_similarity()` 既有可复用
- [x] `FTS5Search.search()` 降级路径既有
- [x] CLI `--mode` 选项既有（增 `semantic` 枚举值）
- [x] workspace 隔离覆盖（WHERE workspace_id=?）
- [x] AC 覆盖 3/3
- [x] 降级策略完备（4 种条件全覆盖）
- [ ] 向量检索 P99 延迟 [TBD]（05 实施后 benchmark）
