---
id: SPEC-F-R-2
title: 真实 embedding benchmark 脚本（semantic vs BM25 召回 + P99 + cache 命中率）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-06"
prd_ref: docs/prd/PRD-e2e-tail-v1.13.0.md
pms_ref: .csp/product-spec/PMS-e2e-tail.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-R-2
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-013-ingest-recursion-benchmark.md
adr_ref: .csp/tech-decisions/ADR/ADR-013-ingest-recursion-benchmark.md
ac_coverage: 4/4
related_tasks:
  - .csp/tasks/TASKS-DELTA-v1.13.0.md#T-F-R-2
---

# SPEC-F-R-2: 真实 embedding benchmark 脚本

## 实现 delta（ground 自源码）

> ADR-013 决策二：独立可执行脚本 `scripts/benchmark_semantic.py`，用真实 vLLM API 真测，不 mock。

### 改动点

| 文件 | 行 | 现状 | 改为 |
|---|---|---|---|
| `scripts/benchmark_semantic.py` | — | 不存在（既有 `tests/unit/test_embedding_benchmark.py:26,44` 用 `_topic_vec` mock 假向量） | 新建独立可执行脚本：vLLM health check → 建数据集 → BM25 baseline → semantic 查询 → P99 统计 → cache 命中率 → 输出结构化结果 |
| `tests/unit/test_embedding_benchmark.py` | `:26` `_topic_vec` / `:44` `_mock_embedding_response` | mock 假向量（非真实 API），retrospective Q2 finding | 保留 mock 版作 CI 单元测试（验证逻辑路径）；真实 benchmark 由 `scripts/benchmark_semantic.py` 承担（不 mock） |

### 不改动

- `embed_texts()` provider 接口不变（v1.12.0 已 pivot 到 API，httpx 直连 vLLM）。
- `QueryEngine._semantic_search()`（`engine.py:458-589`）+ `_keyword_search()`（`engine.py:212-300`）逻辑不变——benchmark 调用既有方法，不新写检索逻辑。
- embedding_store 表结构不变（BLOB + dim + model + workspace_id，ADR-010）。
- semantic cache 逻辑不变（ADR-011，`get_cache()` + `mode="semantic"` key 隔离）。

## 后端架构

### 脚本入口（`scripts/benchmark_semantic.py`）

```python
#!/usr/bin/env python3
"""Benchmark: semantic vs BM25 recall + P99 latency + cache hit rate.

Uses REAL vLLM API (qwen_embedding@8001) — no mock.
Run: python scripts/benchmark_semantic.py [--vllm-base http://localhost:8001]

AC-B-1..4 (F-R-2).
"""
```

**执行流程**：

1. **health check vLLM 8001**：`httpx.get(f"{vllm_base}/health")` 或 `httpx.post(f"{vllm_base}/v1/embeddings", json={"model":"qwen_embedding","input":["probe"]})`。不可达 → print "vLLM embedding endpoint at :8001 unreachable. Start vLLM then re-run." → `sys.exit(1)`（AC-B-4，不 mock）。
2. **建测试数据集**：≥3 主题域（ML / crypto / web），每主题 ≥5 文档（共 ≤15 文档，量小不 OOM）。文档含同义表述（如 "machine learning" 文档不含 "AI" 字面，但语义相关——BM25 漏、semantic 应召回）。ingest 到临时 wiki（`apply_migrations` + insert claims + FTS5 + embedding_store）。
3. **BM25 baseline 查询**：对查询集逐条调 `_keyword_search()`（`engine.py:212`，FTS5 BM25），统计召回（相关文档数）。
4. **semantic 查询**：对同一查询集逐条调 `_semantic_search()`（`engine.py:458`，cosine），统计召回。清 cache 后跑（确保非命中 cache 的真实检索延迟）。
5. **P99 延迟**：对同一查询跑 N≥100 次（semantic + BM25 各跑），`time.perf_counter()` 统计 P99。semantic P99 须优于或接近 BM25 P99（目标 [TBD] ms，跑完填实际值）。
6. **cache 命中率**：同一查询跑 2 次——第 1 次 miss（延迟含 embed+检索），第 2 次应命中 cache（`_cache.get` 命中，`engine.py:486-489`），延迟显著降低。统计 hit/miss。
7. **输出结构化结果**：JSON/表格——`recall_semantic` / `recall_bm25` / `p99_ms` / `cache_hit_rate` + 查询集明细。

### 数据集（HOW，本 Spec 定）

| 主题 | 文档（≥5） | 同义查询 |
|---|---|---|
| ML | "machine learning models for prediction" / "training neural networks on large datasets" / "deep learning architectures for vision" / "gradient descent optimization" / "transformer attention mechanism" | "AI"（文档不含 "AI" 字面，BM25 漏，semantic 应召回） |
| crypto | "Ed25519 signatures in cryptography" / "elliptic curve algorithm for security" / "asymmetric encryption keys" / "digital signature verification" / "hash function collision resistance" | "public key security"（同义） |
| web | "REST API design patterns" / "FastAPI web framework" / "HTTP server building" / "frontend backend separation" / "stateless authentication" | "web service architecture"（同义） |

**召回判定**：同义查询应召回对应主题的 ≥3 文档（top-K 内）。BM25 在同义查询上召回低（字面不匹配），semantic 应高（语义相关）。

### P99 统计方法

```python
import time

def measure_p99(query_fn, query, n=100):
    """Measure P99 latency of a query function (seconds)."""
    latencies = []
    for _ in range(n):
        t0 = time.perf_counter()
        query_fn(query)
        latencies.append(time.perf_counter() - t0)
    latencies.sort()
    p99_idx = int(len(latencies) * 0.99)
    return latencies[p99_idx]
```

**注意**：P99 跑 semantic 时须清 cache（否则第 2 次起命中 cache，测的是 cache 延迟而非检索延迟）。cache 命中率测试单独跑（不清 cache，第 2 次命中）。

### cache 命中率测试

```python
def measure_cache_hit(query_fn, query):
    """Run same query twice; 2nd should hit cache (lower latency)."""
    # Clear cache, run 1st (miss)
    from saw.engines.query.cache import get_cache
    cache = get_cache()
    cache.clear()  # ensure clean
    t0 = time.perf_counter()
    result1 = query_fn(query)
    lat1 = time.perf_counter() - t0
    # Run 2nd (should hit cache)
    t0 = time.perf_counter()
    result2 = query_fn(query)
    lat2 = time.perf_counter() - t0
    hit = lat2 < lat1 * 0.5  # 2nd significantly faster → cache hit
    return {"first_ms": lat1*1000, "second_ms": lat2*1000, "hit": hit}
```

### vLLM 接入（复用既有 API 路径）

benchmark 走 `embed_texts()` API 路径（v1.12.0 已 pivot，httpx 直连 vLLM）。设置 env：
- `SAW_EMBEDDING_MODEL=qwen_embedding`
- `EMBEDDING_API_KEY=dummy`（vLLM 本地不验 key）
- `SAW_EMBEDDING_API_BASE=http://localhost:8001/v1`（benchmark 可配 `--vllm-base`）

不依赖本地 torch/SentenceTransformer（PRD NFR，benchmark 走 API 路径）。

### 输出格式

```json
{
  "vllm_endpoint": "http://localhost:8001",
  "dataset": {"topics": 3, "docs_per_topic": 5, "total_docs": 15},
  "recall": {
    "semantic": {"ML_query": 3, "crypto_query": 3, "web_query": 3, "avg": 3.0},
    "bm25": {"ML_query": 0, "crypto_query": 1, "web_query": 2, "avg": 1.0}
  },
  "p99_ms": {"semantic": 42.5, "bm25": 15.3},
  "cache": {"first_ms": 45.2, "second_ms": 0.8, "hit": true},
  "query_details": [...]
}
```

## 异常处理

| 场景 | 处理 | 用户提示 |
|---|---|---|
| vLLM 8001 不可达 | health check 失败 → 报错退出，不 mock | "Error: vLLM embedding endpoint at :8001 unreachable. Start vLLM then re-run." |
| API 超时 | 记超时，跳过该查询，继续 | "Warning: query N timed out, skipped" |
| API 返回维度不匹配 | 报错退出 | "Error: embedding dim mismatch (expected X, got Y)" |

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-B-1（真实 API 召回） | `tests/unit/test_embedding_benchmark.py`（标 `@pytest.mark.benchmark_e2e`，CI 无 vLLM skip）：真 vLLM 可达时跑 `scripts/benchmark_semantic.py` 逻辑 → semantic 召回 ≥ BM25（同义查询集） | recall_semantic ≥ recall_bm25 |
| AC-B-2（P99 延迟） | `test_embedding_benchmark.py`（标 marker，skip if no vLLM）：跑 benchmark P99 统计 → 输出 P99 数值，记录 baseline | p99_ms 输出数值（[TBD] 跑完填） |
| AC-B-3（cache 命中率） | `test_embedding_benchmark.py`（标 marker，skip if no vLLM）：同查询跑 2 次 → 第 2 次命中 cache，延迟显著低，输出 hit/miss | second_ms < first_ms * 0.5 + hit=true |
| AC-B-4（vLLM 不可达报错） | `test_embedding_benchmark.py`：mock vLLM 不可达 → benchmark 报 "vLLM endpoint unreachable" 退出，不 mock | sys.exit(1) + stderr 含 "unreachable" |

**CI 兼容**：AC-B-1/2/3 标 `@pytest.mark.benchmark_e2e`（或 `importorskip` vLLM 可达），CI 无 vLLM 时 skip（不影响 CI 绿）。AC-B-4 不依赖 vLLM（mock 不可达），CI 始终跑。既有 mock 版 `test_benchmark_semantic_vs_bm25_recall` / `test_benchmark_p99_latency_mock` 保留（验证逻辑路径，CI 跑）。

## 实现就绪度

- [x] 脚本入口明确（`scripts/benchmark_semantic.py`，可执行）
- [x] vLLM 接入复用 `embed_texts()` API 路径（httpx 直连，ADR-012）
- [x] 检索复用 `_semantic_search` + `_keyword_search`（不新写逻辑）
- [x] 数据集定（3 主题 × 5 文档，同义查询集）
- [x] P99 统计方法定（N≥100，清 cache 后跑）
- [x] cache 命中率方法定（同查询 2 次，第 2 次命中）
- [x] vLLM 不可达报错退出不 mock（AC-B-4）
- [x] CI 兼容（marker skip，AC-B-4 不依赖 vLLM）
- [x] AC 覆盖 4/4
- [ ] P99 目标值 [TBD] ms（跑完填实际值）
- [ ] cache 命中率 [TBD]%（跑完填实际值）
