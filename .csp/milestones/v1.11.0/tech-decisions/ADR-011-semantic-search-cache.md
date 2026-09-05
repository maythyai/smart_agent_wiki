# ADR-011: Semantic Search Cache 策略

## 状态：Accepted

## 上下文

v1.10.0 引入 semantic search（`_semantic_search`），每次查询执行全量 `embed_texts()` + cosine 相似度计算。
07 复盘 finding **N7**（P3）指出：`_semantic_search` 不走 cache，而同文件 `_keyword_search` 已有 F-QS-07 cache 路径。
重复语义查询在大型库下会慢于 BM25（BM25 走 cache 命中，semantic 每次全量 cosine）。
v1.11.0 PRD §3.1 要求 semantic search 复用 F-QS-07 cache 路径，TTL + 索引变更失效。

### CMS 出处（ground 自源码）

| 事实 | file:line | 现状 |
|---|---|---|
| `_keyword_search` cache.get | `src/saw/engines/query/engine.py:223-237` | `from saw.engines.query.cache import get_cache` → `_cache.get(question, _cache_params)`，`_cache_params` 含 `mode="search"` + `workspace_id` + `limit` + `offset` |
| `_keyword_search` cache.set | `src/saw/engines/query/engine.py:299-300` | `_cache.set(question, _cache_params, _qr)` — TTL 由 cache 模块默认 300s |
| cache key 构造 | `src/saw/engines/query/cache.py:38-49` | `_make_key(query, params)` → `hashlib.sha256(json.dumps({"query": query, "params": params}, sort_keys=True))` — params 含 mode + workspace_id + limit + offset |
| cache TTL | `src/saw/engines/query/cache.py:22` | `default_ttl=300`（5 分钟），`set()` 可传 `ttl` 覆盖 |
| cache 失效机制 | `src/saw/engines/query/cache.py:89-91` | `clear()` 全量清空（TTL 过期自动逐条；`clear()` 用于内容写入/rebuild 触发） |
| `_semantic_search` 无 cache | `src/saw/engines/query/engine.py:330-420` | 入口直接 `embed_texts()` → 全量 cosine，无 `cache import/get/set` |
| `rebuild-embeddings` 既有 cache invalidation 钩子 | F-N-1 实现 | rebuild 命令清 `embedding_store` 表时应同时 `cache.clear()` |
| cache 单例 | `src/saw/engines/query/cache.py:96-104` | `get_cache()` 全局单例 `_cache`，`_keyword_search` 和 `_semantic_search` 共享同一实例 |

## 决策

### 推荐候选 ①：复用 F-QS-07 cache 单例，同 key 域（mode="semantic" 隔离）

`_semantic_search` 入口插入 `cache.get` / `cache.set`，复用既有 `QueryCache` 单例（`get_cache()`），
cache params 中 `mode="semantic"` 与 `_keyword_search` 的 `mode="search"` 天然隔离——
`_make_key()` 以 `params` 全量参与 SHA256，不同 mode → 不同 key → 不冲突。

cache key params：
```python
_cache_params = {
    "limit": limit,
    "offset": offset,
    "mode": "semantic",           # ← 与 keyword 的 "search" 隔离
    "workspace_id": self._workspace_id,  # ← 防 cross-workspace 泄漏（与 _keyword_search 对称）
}
```

TTL：复用 `QueryCache.default_ttl=300`（5 分钟），不单独设 semantic TTL——语义结果与 keyword 结果的
"新鲜度"需求同量级（TTL 内无内容写入即视为有效）。

失效条件（同 F-QS-07）：
1. **TTL 过期**：cache 模块自动逐条淘汰。
2. **内容写入触发 clear**：claim/wiki ingest 时 `cache.clear()` 全量清空（既有钩子）。
3. **embedding 索引重建触发 clear**：`rebuild-embeddings` 命令执行时 `cache.clear()`（须在 rebuild 实现中补 `get_cache().clear()` 调用）。

命中逻辑：
```python
_cached = _cache.get(question, _cache_params)
if _cached is not None:
    return _cached
# ... embed + cosine + 排序 ...
_cache.set(question, _cache_params, _qr)
return _qr
```

不缓存的条件：
- `semantic_fallback=True`（降级到 BM25）：降级结果已走 `_keyword_search` 自身 cache，不重复缓存。
- `index_empty=True`（空索引）：避免空索引状态被缓存阻塞后续重建。

## 备选方案

| 方案 | 优势 | 劣势 | 适用条件 |
|---|---|---|---|
| **① 复用 F-QS-07 cache 单例，mode="semantic" 隔离（选）** | 零新依赖，复用既有 `QueryCache` / `get_cache()` / `clear()` 钩子；失效逻辑天然与 keyword 对称；代码改动最小（6 行 get + 1 行 set）；cache stats 统一 | semantic 与 keyword 共享 max_size=1000，极端场景下互相驱逐 | 本轮 additive MINOR，低风险优先，cache 单例已够用 ✓ |
| ② 独立 semantic cache dict | semantic cache 独立 max_size / TTL，不与 keyword 互相驱逐 | 需新建 `SemanticQueryCache` 类或第二实例，代码改动大；失效逻辑须复制一份；维护成本高 | 语义查询量远大于 keyword 查询时（本轮无此场景） |

## 理由

1. **复用优先**（选型六原则②轻量优于重量）：候选 ① 零新类/新实例，仅在 `_semantic_search` 入口加 `cache.get` + 出口加 `cache.set`，改动 ~8 行（参照 `_keyword_search` L223-237/L299-300 范式），是最轻量方案。
2. **key 隔离已天然覆盖**：`_make_key()` 以 `params` 全量参与 SHA256，`mode="semantic"` vs `mode="search"` → 不同 hash → 不同 key。workspace_id 也入 key，跨 workspace 不泄漏（与 `_keyword_search` L228-232 对称）。
3. **失效逻辑对称**：F-QS-07 的 `cache.clear()` 钩子（内容写入触发）天然清空 semantic cache（同一实例），无须额外失效逻辑。唯一需补：`rebuild-embeddings` 命令中调 `get_cache().clear()`。
4. **TTL 同量级合理**：semantic 结果的"新鲜度"需求与 keyword 同量级——TTL 内无内容写入即有效。向量结果"更易 stale"的风险由内容写入 `clear()` 覆盖（ingest 即 clear），不依赖更短 TTL。
5. **max_size 共享可接受**：本轮 local-first 小库场景，cache 条目数远低于 1000 上限，互相驱逐风险可忽略。若未来 semantic 查询量暴增，可升级到候选 ②（不改变 API 契约）。

## 后果

### 正面
- semantic 重复查询走 cache，跳过 `embed_texts()` + 全量 cosine，延迟从"全量计算"降到"dict lookup"。
- 失效逻辑与 F-QS-07 完全对称，维护一份 clear 钩子即可。
- workspace 隔离覆盖（cache key 含 workspace_id）。
- cache stats 统一（`QueryCache.stats()` 含 semantic + keyword 命中率）。

### 负面
- semantic 与 keyword 共享 max_size=1000，极端场景下互相驱逐（本轮可接受，升级路径 = 候选 ②）。
- `rebuild-embeddings` 命令须补 `cache.clear()` 调用（一行，F-N-1 既有实现可能未调）。

### 风险
- **rebuild-embeddings 未调 clear**：若 F-N-1 实现中 rebuild 命令未调 `get_cache().clear()`，重建后旧 cache 仍命中 → stale 结果。缓解：SPEC-F-O-1 明确要求 rebuild 路径补 clear 钩子。
- **降级结果误缓存**：`semantic_fallback=True` 的降级结果若写入 semantic cache，后续 embeddings 恢复后仍返回 BM25 结果。缓解：降级路径在 `cache.set` 之前 return，不写 cache。
- **空索引结果误缓存**：`index_empty=True` 的空结果若缓存，重建后仍返回空。缓解：空索引路径在 `cache.set` 之前 return。

## 关联 Feature
F-O-1（semantic cache）、F-N-1（rebuild-embeddings 须补 cache.clear 钩子）、F-N-2（_semantic_search 既有实现，加 cache 包装）
