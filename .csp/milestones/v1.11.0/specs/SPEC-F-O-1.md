---
id: SPEC-F-O-1
title: semantic search 走 query cache（复用 F-QS-07，TTL + 索引变更失效）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-05"
prd_ref: docs/prd/PRD-debt-closure-v1.11.0.md
pms_ref: .csp/product-spec/PMS-debt-closure.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-O-1
complexity: M
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
adr_ref: .csp/tech-decisions/ADR/ADR-011-semantic-search-cache.md
ac_coverage: 4/4
related_tasks: [.csp/tasks/TASKS-DELTA-v1.11.0.md#T-F-O-1]
---

# SPEC-F-O-1: semantic search 走 query cache

## 实现 delta（ground 自源码）

- **插入点**：`src/saw/engines/query/engine.py` `_semantic_search` 方法（L~330–420）入口处加 `cache.get`，出口处加 `cache.set`，参照同文件 `_keyword_search`（L223-237 `cache.get` / L299-300 `cache.set`）范式。
- **复用** `src/saw/engines/query/cache.py::get_cache()` 全局单例（L96-104），`QueryCache` 类（L18-91）——`_make_key()` 以 params 全量参与 SHA256，`mode="semantic"` 与 `mode="search"` 天然隔离。
- **TTL**：复用 `QueryCache.default_ttl=300`（5 分钟），不单独设 semantic TTL。
- **失效**：复用 F-QS-07 既有 `cache.clear()` 钩子（内容写入触发）；rebuild-embeddings 命令中补 `get_cache().clear()` 调用（若 F-N-1 实现未调）。
- **不缓存**：`semantic_fallback=True`（降级到 BM25）和 `index_empty=True`（空索引）的结果不写 cache。

## 后端架构

### cache 插入伪代码（`_semantic_search` 改动）

```python
def _semantic_search(self, question: str, limit: int = 20, offset: int = 0) -> QueryResult:
    # ── NEW: cache.get（参照 _keyword_search L223-237）──
    from saw.engines.query.cache import get_cache
    _cache = get_cache()
    _cache_params = {
        "limit": limit,
        "offset": offset,
        "mode": "semantic",
        "workspace_id": self._workspace_id,
    }
    _cached = _cache.get(question, _cache_params)
    if _cached is not None:
        return _cached
    # ── END NEW ──

    # 1. Tier check: degrade to BM25 if embeddings unavailable
    if not embeddings_available():
        result = self._keyword_search(question, limit=limit, offset=offset)
        result.mode = "semantic_fallback"
        result.meta = {**(result.meta or {}), "semantic_fallback": True}
        return result  # ← 不写 cache（降级结果走 keyword 自身 cache）

    # 2. Embed query text
    vecs = embed_texts([question])
    if vecs is None:
        result = self._keyword_search(question, limit=limit, offset=offset)
        result.mode = "semantic_fallback"
        result.meta = {**(result.meta or {}), "semantic_fallback": True, "embedding_error": True}
        return result  # ← 不写 cache

    query_vec = vecs[0]

    # 3. Load all vectors for this workspace
    rows = self._conn.execute(
        "SELECT doc_id, vector, dim FROM embedding_store WHERE workspace_id = ?",
        (self._workspace_id,),
    ).fetchall()

    if not rows:
        return QueryResult(
            answer="Embedding index is empty. Run `saw rebuild-embeddings` to build it.",
            mode="semantic",
            meta={"semantic_fallback": False, "index_empty": True},
        )  # ← 不写 cache（空索引，避免阻塞后续重建）

    # 4. Compute cosine similarity, sort, take top-K
    scored = []
    for doc_id, blob, dim in rows:
        vec = list(struct.unpack(f"<{dim}f", blob))
        sim = cosine_similarity(query_vec, vec)
        scored.append((doc_id, sim))
    scored.sort(key=lambda x: -x[1])
    top_k = scored[offset : offset + limit]

    # 5. Resolve doc_id → claim/wiki content
    sources = []
    for doc_id, sim in top_k:
        # ... (既有 resolve 逻辑不变)

    _qr = QueryResult(
        answer=(...),
        sources=sources,
        coverage=100.0,
        mode="semantic",
        meta={
            "total": len(sources),
            "limit": limit,
            "offset": offset,
            "semantic_fallback": False,
        },
    )
    # ── NEW: cache.set（参照 _keyword_search L299-300）──
    try:
        _cache.set(question, _cache_params, _qr)
    except Exception as cache_exc:
        logger.warning("semantic cache write failed: %s", cache_exc)
    # ── END NEW ──
    return _qr
```

### cache key 构造

| 参数 | 值 | 说明 |
|---|---|---|
| `query` | question 文本 | 原始查询字符串 |
| `params.mode` | `"semantic"` | 与 keyword 的 `"search"` 隔离 |
| `params.workspace_id` | `self._workspace_id` | 防 cross-workspace 泄漏（与 `_keyword_search` L228 对称） |
| `params.limit` | limit | 分页参数 |
| `params.offset` | offset | 分页参数 |

→ `QueryCache._make_key()` → `SHA256(json.dumps({"query": question, "params": {...}}, sort_keys=True))`

### TTL

| 配置 | 值 | 来源 |
|---|---|---|
| TTL | 300 秒（5 分钟） | `QueryCache.default_ttl=300`（`cache.py:22`） |
| 过期处理 | `datetime.now() > expires_at` → 自动逐条淘汰（`cache.py:66-69`） | 既有逻辑，复用 |

### 失效钩子

| 触发条件 | 失效方式 | 既有/新增 |
|---|---|---|
| TTL 过期 | cache 模块自动逐条淘汰 | 既有 |
| 内容写入（claim/wiki ingest） | `cache.clear()` 全量清空 | 既有钩子（F-QS-07） |
| `rebuild-embeddings` 命令执行 | `get_cache().clear()` 全量清空 | **须确认/补**：F-N-1 rebuild 实现中是否已调 `cache.clear()`；若未调，在 rebuild 命令 finally/commit 前补一行 `get_cache().clear()` |

### 不缓存路径

| 条件 | 原因 |
|---|---|
| `semantic_fallback=True`（embeddings unavailable） | 降级结果已走 `_keyword_search` 自身 cache（`mode="search"` key），不重复缓存到 `mode="semantic"` key |
| `embedding_error=True`（embed_texts 返回 None） | 同上，降级到 BM25 |
| `index_empty=True`（embedding_store 无行） | 空索引状态不应被缓存，否则 rebuild 后仍返回空 |

### 异常处理

| 场景 | 处理 | 用户提示 |
|---|---|---|
| cache 写入失败（DB 锁/异常） | `try/except` catch + `logger.warning`，不阻塞查询返回 | 无（降级为无 cache，查询正常） |
| TTL 过期后首次查询 | cache miss → 正常计算 + 重写 cache | 无（用户无感） |

## API 契约

无新端点。既有端点行为不变（仅加 cache 层）：

- `GET /api/v1/search?mode=semantic` — 既有端点，cache 透明（命中更快，miss 同既有）
- `saw search --mode semantic` — 既有 CLI 命令，cache 透明

返回 schema 不变（`QueryResult` dataclass），`meta` 字段不变（无新增 cache 字段，cache 对用户透明）。

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-CACHE-1（cache 命中） | `tests/unit/test_semantic_cache.py`（新建，mock）：mock `embed_texts` + `cosine_similarity`，首次调用 `_semantic_search` → embed/cosine 被调用 → 再次同查询 → embed/cosine **不**被调用（cache 命中）+ 结果一致 | 命中跳过全量 cosine |
| AC-CACHE-2（workspace 隔离） | `tests/unit/test_semantic_cache.py`（扩）：workspace A 缓存后，workspace B 同查询 → cache miss（独立计算） | 跨 workspace 不泄漏 |
| AC-CACHE-3（索引变更失效） | `tests/unit/test_semantic_cache.py`（扩）：缓存后 → `cache.clear()` → 再次查询 → cache miss（重新计算） | rebuild/ingest 触发 clear 后失效 |
| AC-CACHE-4（fallback 不缓存） | `tests/unit/test_semantic_cache.py`（扩）：mock `embeddings_available()=False` → `_semantic_search` 返回 `semantic_fallback=True` → 检查 cache 无 semantic key（不写 cache） | 降级结果不走 semantic cache |

> 注：AC-CACHE-1/2/3 用 mock（不依赖 sentence_transformers），AC-CACHE-4 降级场景天然不需 SDK。全部 4 AC 可在 CI 无 SDK 环境下 pass。

## 降级策略

| 条件 | 行为 |
|---|---|
| embeddings available（tier=FULL） | cache.get → 命中返回 / miss → embed + cosine → cache.set → 返回 |
| embeddings unavailable | 降级到 `_keyword_search`（走自身 `mode="search"` cache），不写 semantic cache |
| cache 写入异常 | catch + warning 日志，查询正常返回（无 cache 降级） |

## 安全考量

- **workspace 隔离**：cache key 含 `workspace_id`（与 `_keyword_search` L228 对称），跨 workspace 查询 cache miss，不泄漏。
- **cache 透明**：用户不可感知 cache（返回 schema 不变），无敏感信息泄露。

## 实现就绪度

- [x] cache 插入点明确（`_semantic_search` 入口 + 出口，参照 `_keyword_search` 范式）
- [x] cache key 构造明确（mode + workspace_id + limit + offset）
- [x] TTL 复用 F-QS-07 既有配置（300s）
- [x] 失效钩子明确（TTL + ingest clear + rebuild clear）
- [x] 不缓存路径明确（fallback + index_empty）
- [x] 异常处理明确（cache 写入失败 catch + warning）
- [x] AC 覆盖 4/4
- [ ] cache 命中率基线 [TBD]（须 05 实施后 benchmark）
