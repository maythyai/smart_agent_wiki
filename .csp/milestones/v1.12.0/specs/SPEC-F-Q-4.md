---
id: SPEC-F-Q-4
title: 测试改 API mock + benchmark semantic vs BM25
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-05"
prd_ref: docs/prd/PRD-embedding-api-v1.12.0.md
pms_ref: .csp/product-spec/PMS-embedding-api.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-Q-4
complexity: M
tdd_ref: .csp/tech-decisions/ADR/ADR-012-embedding-provider-api.md
adr_ref: .csp/tech-decisions/ADR/ADR-012-embedding-provider-api.md
ac_coverage: 3/3
related_tasks:
  - .csp/tasks/TASKS-DELTA-v1.12.0.md#T-F-Q-4
---

# SPEC-F-Q-4: 测试改 API mock + benchmark

## 实现 delta（ground 自源码）

> v1.10.0 的 7 个 importorskip 测试在 CI 全 skip（N1 High/P1）。本 Spec 将其改为 API mock 测试，CI 全 pass 不 skip，并新增 benchmark。

### 改动点

| 文件 | 行 | 现状 | 改为 |
|---|---|---|---|
| `tests/unit/test_embedding_index.py:6` | `pytest.importorskip("sentence_transformers")` | 首行 importorskip，CI 全 skip | 删 importorskip，改 mock `litellm.embedding` 返回固定 1536 维向量 |
| `tests/unit/test_semantic_search.py:6` | `pytest.importorskip("sentence_transformers")` | 首行 importorskip，CI 全 skip | 删 importorskip，改 mock `litellm.embedding` 返回固定向量 |
| `tests/unit/test_related_pages_embedding.py:6` | `pytest.importorskip("sentence_transformers")` | 首行 importorskip，CI 全 skip | 删 importorskip，改 mock `litellm.embedding` 返回固定向量 |
| `tests/unit/test_embedding_degradation.py` | mock `embeddings_available` return False | mock 目标仅覆盖 ST 不可用 | mock 目标扩展到 API 不可用场景 |
| `tests/unit/test_ci_workflow.py` | importorskip 检测逻辑含 embedding | embedding 测试 importorskip ST | 更新——embedding 测试不再 importorskip ST |
| 新建 `tests/unit/test_embedding_benchmark.py` | 不存在 | — | 新增 benchmark：semantic vs BM25 召回 + P99（mock 数据） |

### 不改动

- `[learn]` extra 的其他 importorskip 先例不变（`test_fsrs.py` / `test_trends.py` / `test_distiller.py` 的 importorskip 保留——那些是 `[learn]` extra 的其他用途，非 embedding）。
- `test_embedding_degradation.py` 的 4 个既有降级测试 mock 范式不变，仅扩展 mock 目标。

## 后端架构

### mock 策略

**mock 目标**：`litellm.embedding`（在 `saw.adapters.embeddings` 模块中 patch）。

```python
from unittest.mock import patch, MagicMock

def _mock_embedding_response(dim=1536):
    """Create a mock litellm.embedding response with fixed-dim vectors."""
    response = MagicMock()
    response.data = [
        {"embedding": [0.01 * (i + 1) / dim for i in range(dim)], "index": 0},
    ]
    return response

# In test:
with patch("saw.adapters.embeddings.litellm.embedding", return_value=_mock_embedding_response()):
    vecs = embed_texts(["test text"])
    assert vecs is not None
    assert len(vecs[0]) == 1536
```

**mock 向量设计**：
- 固定 dim=1536（模拟 `text-embedding-3-small`）。
- 向量值有区分度（不同文本返回不同向量），使 cosine 排序有意义。
- L2-normalized（mock 向量已 normalize，或 `embed_texts()` 内 `_normalize()` 处理）。

### test_embedding_index.py（3 测试，改）

| 测试 | 现状（importorskip） | 改后（API mock） |
|---|---|---|
| `test_emb_ac1_ingest_writes_embedding` | importorskip ST → EmbeddingSink.write → assert dim=384 | mock `litellm.embedding` → EmbeddingSink.write → assert dim=1536 + model=mock model 名 |
| `test_emb_ac3_rebuild_skips_deleted` | importorskip ST → embed_texts → 2 vectors | mock `litellm.embedding` → embed_texts → 2 vectors（deleted skip） |
| `test_embedding_sink_upsert` | importorskip ST → 2 次 write → 1 row | mock `litellm.embedding` → 2 次 write → 1 row（upsert） |

### test_semantic_search.py（2 测试，改）

| 测试 | 现状（importorskip） | 改后（API mock） |
|---|---|---|
| `test_sem_ac1_returns_semantic_results` | importorskip ST → embed_texts → cosine 排序 | mock `litellm.embedding` → embed_texts → cosine 排序 |
| `test_sem_ac3_empty_index` | importorskip ST → empty index → index_empty | mock `litellm.embedding` → empty index → index_empty |

### test_related_pages_embedding.py（2 测试，改）

| 测试 | 现状（importorskip） | 改后（API mock） |
|---|---|---|
| `test_link_ac1_semantic_suggestion` | importorskip ST → embed_texts → semantic similarity reason | mock `litellm.embedding` → embed_texts → semantic similarity reason |
| `test_link_ac3_dissimilar_ranks_lower` | importorskip ST → embed_texts → ranking | mock `litellm.embedding` → embed_texts → ranking |

### test_embedding_degradation.py（4 测试，扩）

| 测试 | 现状 | 改后 |
|---|---|---|
| `test_emb_ac2_no_learn_no_error` | mock `embeddings_available()=False` → skip | 扩展：也 mock API 不可用（`_api_embedding_available()=False`）+ ST 不可用 → skip |
| `test_sem_ac2_degrades_to_bm25` | mock `embeddings_available()=False` → BM25 | 扩展：API + ST 都不可用 → BM25 |
| `test_link_ac2_no_learn_keeps_3signal` | mock `embeddings_available()=False` → 3-signal | 扩展：API + ST 都不可用 → 3-signal |
| `test_sem_ac3_empty_index_with_embeddings_unavailable` | mock `embeddings_available()=False` → fallback | 扩展：API + ST 都不可用 → fallback |

### 新增 benchmark 测试（`tests/unit/test_embedding_benchmark.py`）

```python
"""Benchmark: semantic vs BM25 recall + P99 (API mock, no real API key needed).

Real E2E benchmark requires user to configure a real API key and run:
    pytest tests/unit/test_embedding_benchmark.py --benchmark-e2e
"""
import sqlite3
import struct
import time
from unittest.mock import patch, MagicMock

import pytest


def test_benchmark_semantic_vs_bm25_recall():
    """AC-TEST-3: benchmark semantic vs BM25 recall on synonym query set.

    Uses API mock vectors with known similarity structure to verify
    semantic search recalls synonym-matched docs that BM25 misses.
    """
    # Setup: mock litellm.embedding with structured vectors
    # - "machine learning" docs → high-similarity vectors
    # - "cryptography" docs → low-similarity vectors
    # Query "AI" (synonym for "machine learning") → semantic should recall ML docs
    # BM25 on "AI" → may miss if docs don't contain "AI" literally
    ...


def test_benchmark_p99_latency_mock():
    """AC-TEST-3: benchmark semantic search P99 latency (mock, baseline [TBD]).

    Mock litellm.embedding has ~0ms latency. Real API P99 requires E2E.
    Records baseline [TBD] for real API comparison.
    """
    ...
```

### test_ci_workflow.py 更新

- importorskip 检测逻辑中，embedding 测试不再 `importorskip("sentence_transformers")`。
- CI workflow 不再需要 `[learn]` extra 跑 embedding 测试。

## 测试策略

### 测试金字塔

| 层 | 用例 | mock 策略 |
|---|---|---|
| 单元（≥80%） | test_embedding_index.py（3）+ test_semantic_search.py（2）+ test_related_pages_embedding.py（2）+ test_embedding_degradation.py（4）+ test_embedding_benchmark.py（2） | mock `litellm.embedding` / mock `embeddings_available` |
| 集成 | 既有 smoke 6/6 | 不变 |
| E2E | 可选：用户配真实 API key 跑 benchmark | 真实 API call |

### mock vs 真实 API 行为偏差缓解

- mock 验证逻辑路径（向量入库、cosine 排序、空索引、维度变更、upsert、降级）。
- 真实 API key 可选 E2E benchmark 补充（`--benchmark-e2e` flag）。
- mock 维度与实际 API dim 一致（固定 1536 维）。

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-TEST-1（CI embedding 测试全 pass） | `tests/unit/test_embedding_index.py` + `test_semantic_search.py` + `test_related_pages_embedding.py`（改）：去 importorskip，mock `litellm.embedding` → 全 pass（不 skip） | CI 全 pass 不 skip |
| AC-TEST-2（CI 无 importorskip） | `tests/unit/test_ci_workflow.py`（扩）：检查 embedding 测试无 `importorskip("sentence_transformers")` | 无 importorskip + CI 不需 `[learn]` extra |
| AC-TEST-3（benchmark 可执行） | `tests/unit/test_embedding_benchmark.py`（新建）：mock 向量集 → semantic vs BM25 召回对比 + P99 延迟 | 输出召回率 + P99（mock baseline [TBD]） |

## 实现就绪度

- [x] 7 个 importorskip 测试改动点明确（3 文件首行 `importorskip`）
- [x] 4 个降级测试扩展点明确（mock 目标从 `embeddings_available` 扩到 API 不可用）
- [x] mock 策略设计完整（mock `litellm.embedding` 返回固定 dim 向量）
- [x] benchmark 测试设计完整（semantic vs BM25 召回 + P99）
- [x] `test_ci_workflow.py` 更新点明确
- [x] AC 覆盖 3/3
- [ ] benchmark baseline [TBD]（mock 延迟为 0，真实 E2E benchmark 须用户配 API key 可选跑）
- [ ] semantic vs BM25 召回率 [TBD]（须同义查询集 benchmark 后定 baseline）
