---
id: SPEC-F-S-3
title: benchmark 更新（cache 真实度量 + ANN vs cosine 对比 + 规模延迟曲线）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-06"
prd_ref: docs/prd/PRD-semantic-perf-v1.14.0.md
pms_ref: .csp/product-spec/PMS-semantic-perf.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-S-3
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-014-ann-vector-index.md
adr_ref: .csp/tech-decisions/ADR/ADR-014-ann-vector-index.md
ac_coverage: 5/5
related_dependencies:
  - F-S-2 (ANN 索引路径实现完成后才能跑 ANN vs cosine 对比)
related_tasks: [".csp/tasks/TASKS-DELTA-v1.14.0.md (T-F-S-3)"]
---

# SPEC-F-S-3: benchmark 更新

## 实现 delta（ground 自源码）

> ADR-013（Accepted）benchmark 方法论不变：独立可执行脚本 `scripts/benchmark_semantic.py`，真实 vLLM API。
> ADR-014 cosine 改进 + ANN 路径：benchmark 新增 ANN vs cosine 对比 + 规模延迟曲线。

### 改动点

| 文件 | 现状（ground） | 改为 |
|---|---|---|
| `scripts/benchmark_semantic.py` `_semantic_search` 函数 | 独立函数，直接 `embed_texts()` + cosine，不 import `get_cache`，不经过 `QueryEngine` cache 路径 | 改为通过 `QueryEngine._semantic_search` 跑查询（经过生产 cache 路径），度量真实 cache 行为 |
| `scripts/benchmark_semantic.py` `_measure_cache_hit` 函数 | `"hit": lat2 < lat1 * 0.5`——延迟比较 50% 阈值，非生产 cache 行为 | 改为检查 `cache.stats().hits` 计数（第 1 次后 hits 增加=miss→write；第 2 次后 hits 再增加=hit） |
| `scripts/benchmark_semantic.py` `run_benchmark` 函数 | 仅有 recall + P99 + cache（延迟比较） | 新增 ANN vs cosine P99 对比 + 100/500/1000/5000 规模延迟曲线（`scale_curve`） |
| `scripts/benchmark_semantic.py` 输出格式 | `recall` + `p99_ms` + `cache` + `query_details` | 新增 `ann_p99_ms` / `cosine_p99_ms` / `scale_curve: [{doc_count, p99_ms}, ...]` |

### 不改动

- `_health_check` / `_setup_env` / `_build_db` / `_bm25_search`——vLLM health check + env 配置 + DB 构建 + BM25 baseline 不变（ADR-013 既有逻辑）。
- `_DATASET` / `_QUERIES`——既有数据集（3 主题 × 5 文档）不变；规模延迟曲线用合成随机向量数据集（独立于 `_DATASET`）。
- `test_embedding_benchmark.py`——既有 mock 版测试保留（验证逻辑路径，CI 跑）。

## 后端架构

### cache 命中真实度量（改 `_measure_cache_hit`）

```python
def _measure_cache_hit(query_engine, query: str) -> dict:
    """Measure real cache hit via QueryEngine._semantic_search + cache.stats().

    Uses production cache path (QueryEngine._semantic_search), not
    independent function. Checks cache.stats().hits counter, not
    latency comparison.
    """
    from saw.engines.query.cache import get_cache

    cache = get_cache()
    cache.clear()

    # 1st query: miss → writes to cache
    hits_before = cache.stats()["hits"]
    query_engine._semantic_search(query)
    hits_after_1st = cache.stats()["hits"]

    # 2nd query: should hit cache
    query_engine._semantic_search(query)
    hits_after_2nd = cache.stats()["hits"]

    return {
        "hits_before": hits_before,
        "hits_after_1st": hits_after_1st,
        "hits_after_2nd": hits_after_2nd,
        "cache_hit": hits_after_2nd > hits_after_1st,
    }
```

### ANN vs cosine P99 对比

```python
def _measure_ann_vs_cosine(query_engine, query: str, n: int = 100) -> dict:
    """Measure ANN vs cosine P99 latency.

    Forces ANN path by setting SAW_ANN_THRESHOLD=0 (always ANN).
    Forces cosine path by setting SAW_ANN_THRESHOLD=999999 (always cosine).
    """
    import os

    # ANN path
    os.environ["SAW_ANN_THRESHOLD"] = "0"
    ann_p99 = _measure_p99(query_engine._semantic_search, query, n)

    # Cosine path
    os.environ["SAW_ANN_THRESHOLD"] = "999999"
    cosine_p99 = _measure_p99(query_engine._semantic_search, query, n)

    return {
        "ann_p99_ms": round(ann_p99 * 1000, 2),
        "cosine_p99_ms": round(cosine_p99 * 1000, 2),
    }
```

### 规模延迟曲线

```python
def _measure_scale_curve(query_engine, vllm_base: str) -> list[dict]:
    """Measure semantic P99 at different doc scales.

    Generates synthetic datasets with random vectors (no real embedding)
    at 100/500/1000/5000 docs. Only P99 measurement uses real vLLM.
    """
    scales = [100, 500, 1000, 5000]
    results = []
    for n_docs in scales:
        try:
            # Generate synthetic dataset with random vectors
            conn = _build_synthetic_db(n_docs)
            # Use real vLLM for query embedding only
            p99 = _measure_p99_at_scale(query_engine, conn, n_docs)
            results.append({
                "doc_count": n_docs,
                "p99_ms": round(p99 * 1000, 2),
            })
        except Exception as e:
            # Skip this scale on failure, continue others
            logger.warning("Scale %d failed: %s", n_docs, e)
            continue
    return results
```

### 更新后输出格式

```json
{
  "vllm_endpoint": "http://localhost:8001",
  "dataset": {"topics": 3, "docs_per_topic": 5, "total_docs": 15},
  "recall": {
    "semantic": {"AI": 3, "public key security": 3, "web service architecture": 3, "avg": 3.0},
    "bm25": {"AI": 0, "public key security": 1, "web service architecture": 2, "avg": 1.0}
  },
  "p99_ms": {"semantic": 42.5, "bm25": 15.3},
  "cache": {
    "hits_before": 0,
    "hits_after_1st": 0,
    "hits_after_2nd": 1,
    "cache_hit": true
  },
  "ann_vs_cosine": {
    "ann_p99_ms": 5.2,
    "cosine_p99_ms": 42.5
  },
  "scale_curve": [
    {"doc_count": 100, "p99_ms": 15.2},
    {"doc_count": 500, "p99_ms": 45.3},
    {"doc_count": 1000, "p99_ms": 85.1},
    {"doc_count": 5000, "p99_ms": 12.5}
  ],
  "query_details": [...]
}
```

### 异常处理

| 场景 | 处理 | 用户提示 |
|---|---|---|
| vLLM 不可达 | health check 失败 → 报错退出（exit 1），不 mock | "Error: vLLM embedding endpoint at :8001 unreachable." (AC-C-4) |
| ANN 库未装 | ANN vs cosine 对比中 ann 字段标 `null` | JSON `"ann_p99_ms": null` |
| 合成数据集生成失败 | 跳过该规模，继续其他 | 日志 warning |
| API 超时 | 记超时，跳过该查询 | "Warning: query N timed out, skipped" |

## 测试策略（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-C-1（cache 命中真实度量） | `tests/unit/test_embedding_benchmark.py`（扩）：通过 `QueryEngine._semantic_search` 跑查询 → 检查 `cache.stats().hits` → 第 2 次后 hits 增加（非延迟比较） | `hits_after_2nd > hits_after_1st`，不再用 `lat2 < lat1 * 0.5` |
| AC-C-2（ANN vs cosine 对比） | `test_embedding_benchmark.py`（扩，标 marker skip if no vLLM）：构建 ≥1k 数据集 → 分别跑 ANN 和 cosine → JSON 含 `ann_p99_ms` 和 `cosine_p99_ms` | output dict 含 `ann_p99_ms` + `cosine_p99_ms` |
| AC-C-3（规模延迟曲线） | `test_embedding_benchmark.py`（扩，标 marker）：生成 100/500/1000/5000 数据集 → JSON 含 `scale_curve: [{doc_count, p99_ms}, ...]` | `len(scale_curve) == 4`，每项含 `doc_count` + `p99_ms` |
| AC-C-4（vLLM 不可达报错） | `test_embedding_benchmark.py`（不依赖 vLLM，CI 始终跑）：mock vLLM 不可达 → benchmark 报 "unreachable" 退出 | `sys.exit(1)` + stderr 含 "unreachable" |
| AC-C-5（cache 单元测试 CI 可跑） | `test_embedding_benchmark.py`（不依赖 vLLM，mock embedding）：CI 跑 cache 命中测试 → pass（不 skip） | 测试 pass，无 skip marker |

**CI 兼容**：AC-C-4/AC-C-5 不依赖 vLLM（mock），CI 始终跑。AC-C-1 用 mock embedding（CI 跑）。AC-C-2/AC-C-3 标 `@pytest.mark.benchmark_e2e`，CI 无 vLLM 时 skip。

## 安全考量

- benchmark 走 API 路径（v1.12.0 litellm API），不依赖本地 torch。
- 合成数据集用随机向量（不需真实 embedding），仅 P99 测量用真实 vLLM。
- vLLM 不可达报错退出不 mock（不静默降级）。

## 实现就绪度

- [x] cache 度量改为 `cache.stats().hits` 计数（非延迟比较）
- [x] cache 度量通过 `QueryEngine._semantic_search` 生产路径
- [x] ANN vs cosine P99 对比方案定
- [x] 规模延迟曲线方案定（100/500/1000/5000）
- [x] vLLM 不可达报错退出不 mock（AC-C-4）
- [x] CI 兼容（mock + marker skip）
- [x] AC 覆盖 5/5
- [ ] ANN P99 / cosine P99 实际值 [TBD]（跑完填）
- [ ] 规模延迟曲线实际值 [TBD]（跑完填）
