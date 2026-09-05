# TMS Delta — v1.12.0（2026-09-05）

> 03 测试规约 delta。embedding provider pivot 到 API + E2E 验证 + benchmark。
> 基线：v1.11.0 = 2064 passed / 6 skipped / ruff 0 / coverage 65.36% / smoke 6/6。
> 本轮不依赖 `[learn]` SDK（API mock 跑通全部 embedding 测试，不再 importorskip skip）。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-EA-1（API 配置可用时语义检索） | F-Q-1 | `tests/unit/test_embedding_index.py`（改）：去 importorskip，mock `litellm.embedding` 返回固定 1536 维向量 → EmbeddingSink.write → `SELECT FROM embedding_store` 有行 + dim=1536 + model=mock model 名 | DONE |
| AC-EA-2（API 未配置时降级） | F-Q-1 | `tests/unit/test_embedding_degradation.py`（扩）：mock `_api_embedding_available()=False` + `_st_available()=False` → semantic search → `semantic_fallback: true` + BM25 回退 | DONE |
| AC-DIM-1（维度变更触发重建） | F-Q-2 | `tests/unit/test_embedding_index.py`（改）：mock `litellm.embedding` 返回 1536 维向量 → seed 旧 dim=384 向量 → rebuild → 检测 dim 不匹配 → wipe 旧向量 → 新向量 dim=1536 + model=mock model 名 | DONE |
| AC-DIM-2（ingest 写入正确 model） | F-Q-2 | `tests/unit/test_embedding_index.py`（改）：mock `litellm.embedding` → EmbeddingSink.write → `SELECT model FROM embedding_store` = mock model 名（非 `all-MiniLM-L6-v2`） | DONE |
| AC-FB-1（本地 ST fallback） | F-Q-3 | `tests/unit/test_semantic_search.py`（改）：mock `_api_embedding_available()=False` + `_st_available()=True` + mock `_embed_via_st` → semantic search 返回结果 + `semantic_fallback: false` + 日志提示 "API unavailable, falling back to local ST" | DONE |
| AC-FB-2（无 ST 走 API） | F-Q-3 | `tests/unit/test_semantic_search.py`（改）：mock `litellm.embedding` 返回固定向量 + `_st_available()=False` → semantic search 返回结果 + `semantic_fallback: false` + 无需本地 ST | DONE |
| AC-TEST-1（CI embedding 测试全 pass） | F-Q-4 | `tests/unit/test_embedding_index.py` + `test_semantic_search.py` + `test_related_pages_embedding.py`（改）：去 importorskip，mock `litellm.embedding` → 全 pass（不 skip） | DONE |
| AC-TEST-2（CI 无 importorskip） | F-Q-4 | `tests/unit/test_ci_workflow.py`（扩）：检查 embedding 测试无 `importorskip("sentence_transformers")` → CI 不需 `[learn]` extra | DONE |
| AC-TEST-3（benchmark 可执行） | F-Q-4 | `tests/unit/test_embedding_benchmark.py`（新建）：mock 向量集 → semantic vs BM25 召回对比 + P99 延迟 | DONE |

## 约定

- **API mock 测试**（`test_embedding_index.py` / `test_semantic_search.py` / `test_related_pages_embedding.py`）：去 `pytest.importorskip("sentence_transformers")`，改 `patch("saw.adapters.embeddings.litellm.embedding", ...)` 返回固定 dim（1536）向量，CI 可跑（不 skip、不依赖本地 SDK）。
- **降级测试**（`test_embedding_degradation.py`）：mock 目标从 `embeddings_available` 扩展到也覆盖 API 不可用场景——mock `_api_embedding_available()=False` + `_st_available()=False` → 降级 BM25。
- **benchmark 测试**（`test_embedding_benchmark.py`）：mock `litellm.embedding` 生成固定向量集，对比 semantic vs BM25 召回率 + P99 延迟（mock 延迟为 0，真实 E2E benchmark 须用户配 API key 可选跑）。
- **CI workflow 测试**（`test_ci_workflow.py`）：更新 importorskip 检测逻辑，embedding 测试不再 importorskip ST。
- **`[learn]` extra 其他用途不变**：`test_fsrs.py` / `test_trends.py` / `test_distiller.py` 的 importorskip 保留（非 embedding 相关）。

## 测试文件矩阵

| 测试文件 | mock/importorskip | AC 覆盖 | Feature |
|---|---|---|---|
| `tests/unit/test_embedding_index.py`（改） | mock litellm.embedding（去 importorskip） | AC-EA-1, AC-DIM-1, AC-DIM-2 | F-Q-1, F-Q-2 |
| `tests/unit/test_semantic_search.py`（改） | mock litellm.embedding（去 importorskip） | AC-FB-1, AC-FB-2 | F-Q-3 |
| `tests/unit/test_related_pages_embedding.py`（改） | mock litellm.embedding（去 importorskip） | AC-EA-1（间接） | F-Q-1 |
| `tests/unit/test_embedding_degradation.py`（扩） | mock embeddings_available + API 不可用 | AC-EA-2 | F-Q-1 |
| `tests/unit/test_ci_workflow.py`（扩） | — | AC-TEST-2 | F-Q-4 |
| `tests/unit/test_embedding_benchmark.py`（新建） | mock litellm.embedding | AC-TEST-3 | F-Q-4 |

## 落地状态（05 实施回填，DONE）

全部 9 AC 改造/新建测试用例，状态如下（DONE 05 实施完成回填）：

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-EA-1 | F-Q-1 | `tests/unit/test_embedding_index.py::test_emb_ac1_ingest_writes_embedding`（改 API mock） | DONE |
| AC-EA-2 | F-Q-1 | `tests/unit/test_embedding_degradation.py::test_sem_ac2_degrades_to_bm25`（扩 API 不可用） | DONE |
| AC-DIM-1 | F-Q-2 | `tests/unit/test_embedding_index.py::test_emb_ac3_rebuild_dim_change`（改 API mock + dim 变更） | DONE |
| AC-DIM-2 | F-Q-2 | `tests/unit/test_embedding_index.py::test_emb_ac1_ingest_writes_embedding`（改 assert model 列动态） | DONE |
| AC-FB-1 | F-Q-3 | `tests/unit/test_semantic_search.py::test_sem_fb1_st_fallback`（改 mock API 不可用 + ST 可用） | DONE |
| AC-FB-2 | F-Q-3 | `tests/unit/test_semantic_search.py::test_sem_fb2_no_st_api`（改 mock API + ST 不可用） | DONE |
| AC-TEST-1 | F-Q-4 | `tests/unit/test_embedding_index.py` + `test_semantic_search.py` + `test_related_pages_embedding.py`（去 importorskip 全 pass） | DONE |
| AC-TEST-2 | F-Q-4 | `tests/unit/test_ci_workflow.py::test_no_embedding_importorskip`（扩） | DONE |
| AC-TEST-3 | F-Q-4 | `tests/unit/test_embedding_benchmark.py::test_benchmark_semantic_vs_bm25` + `test_benchmark_p99_latency_mock`（新建） | DONE |
