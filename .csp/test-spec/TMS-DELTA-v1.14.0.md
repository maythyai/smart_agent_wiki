# TMS Delta — v1.14.0（2026-09-06）

> 03 测试规约 delta。semantic 性能优化轮：cache 阈值可配 + ANN 索引替代全量 cosine + benchmark 更新（cache 真实度量 + ANN vs cosine 对比 + 规模延迟曲线）。
> 基线：v1.13.0 = 2179 passed / 3 skipped / 2 deselected (benchmark_e2e) / ruff 0 / coverage 67.27% / smoke 6/6。
> cache 阈值测试用 mock embedding（不依赖 vLLM，CI 跑）；ANN 测试用 mock（CI 跑）；benchmark 真实度量标 marker skip if no vLLM。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-A-1（cache 禁用） | F-S-1 | `tests/unit/test_semantic_cache_config.py`（新建）：设 `SAW_SEMANTIC_CACHE_ENABLED=false`，连续两次相同 semantic 查询 → `cache.stats().hits` 不增加 | mapped |
| AC-A-2（cache 启用默认） | F-S-1 | `test_semantic_cache_config.py`：无 env 或 `=true`，连续两次相同查询 → 第 2 次 `cache.stats().hits` 增加 | mapped |
| AC-A-3（阈值跳过写入） | F-S-1 | `test_semantic_cache_config.py`：设 `SAW_SEMANTIC_CACHE_THRESHOLD_MS=100`，mock API 响应 < 100ms → cache.set 跳过（新查询不写入），cache.get 仍可命中已有缓存 | mapped |
| AC-A-4（向后兼容） | F-S-1 | `test_semantic_cache_config.py`：无任何 `SAW_SEMANTIC_CACHE_*` env → 行为与 v1.13.0 一致（cache 始终启用） | mapped |
| AC-A-5（keyword cache 不受影响） | F-S-1 | `test_semantic_cache_config.py`：设 `SAW_SEMANTIC_CACHE_ENABLED=false`，连续两次相同 keyword 查询 → keyword cache 正常命中（`mode=search` 不受影响） | mapped |
| AC-B-1（ANN 自动切换） | F-S-2 | `tests/unit/test_ann_search.py`（新建）：mock embedding_store 行数 > `SAW_ANN_THRESHOLD` → semantic 查询 → `meta.ann_search: true`，不含 `ann_fallback` | mapped |
| AC-B-2（小规模 cosine） | F-S-2 | `test_ann_search.py`：mock 行数 ≤ `SAW_ANN_THRESHOLD` → semantic 查询 → `meta` 不含 ANN 标记 | mapped |
| AC-B-3（ANN 降级） | F-S-2 | `test_ann_search.py`：mock hnswlib `ImportError` 或索引损坏 → 降级 cosine，`meta.ann_fallback: true`，不报错 | mapped |
| AC-B-4（召回一致性） | F-S-2 | `test_ann_search.py`（标 marker）：构建小数据集，ANN vs cosine top-K 重叠率 ≥95% [TBD] | mapped |
| AC-B-5（related_pages 复用） | F-S-2 | `tests/unit/test_related_pages_ann.py`（新建或扩）：mock 规模 > 阈值 → `compute_related_pages` → 走 ANN 路径，不逐条 SELECT + cosine | mapped |
| AC-C-1（cache 命中真实度量） | F-S-3 | `tests/unit/test_embedding_benchmark.py`（扩）：通过 `QueryEngine._semantic_search` 跑查询 → 检查 `cache.stats().hits` → 第 2 次后 hits 增加（非延迟比较） | mapped |
| AC-C-2（ANN vs cosine 对比） | F-S-3 | `test_embedding_benchmark.py`（扩，标 marker skip if no vLLM）：构建 ≥1k 数据集 → 分别跑 ANN 和 cosine → JSON 含 `ann_p99_ms` 和 `cosine_p99_ms` | mapped |
| AC-C-3（规模延迟曲线） | F-S-3 | `test_embedding_benchmark.py`（扩，标 marker）：生成 100/500/1000/5000 数据集 → JSON 含 `scale_curve: [{doc_count, p99_ms}, ...]` | mapped |
| AC-C-4（vLLM 不可达报错） | F-S-3 | `test_embedding_benchmark.py`（不依赖 vLLM，CI 始终跑）：mock vLLM 不可达 → benchmark 报 "unreachable" 退出 | mapped |
| AC-C-5（cache 单元测试 CI 可跑） | F-S-3 | `test_embedding_benchmark.py`（不依赖 vLLM，mock embedding）：CI 跑 cache 命中测试 → pass（不 skip） | mapped |

## 约定

- **cache 阈值配置测试**（`test_semantic_cache_config.py`，新建）：设/不设 env var，连续两次相同查询，检查 `cache.stats().hits` 计数变化。全部用 mock embedding（不依赖 vLLM），CI 始终跑。每测试前后 `cache.clear()` 确保干净状态。
- **ANN 搜索测试**（`test_ann_search.py`，新建）：mock embedding_store 行数 + mock hnswlib 索引。AC-B-1/2/3 用 mock（CI 跑）。AC-B-4 召回率验证构建小数据集（mock 向量）。hnswlib 须 `pip install hnswlib`（CI 装 `[semantic]` extra）；未装时 ANN 测试标 skip，cosine 路径测试仍跑。
- **related_pages ANN 测试**（`test_related_pages_ann.py`，新建或扩）：mock 规模 > 阈值 → `compute_related_pages` → 断言不执行逐条 SELECT + cosine，走批量/ANN 路径。
- **benchmark cache 真实度量测试**（`test_embedding_benchmark.py`，扩）：AC-C-1 用 mock embedding（CI 跑），通过 `QueryEngine._semantic_search` 跑查询，检查 `cache.stats().hits` 计数——不再用 `lat2 < lat1 * 0.5` 延迟比较。
- **benchmark ANN vs cosine + 规模曲线测试**（`test_embedding_benchmark.py`，扩）：AC-C-2/AC-C-3 标 `@pytest.mark.benchmark_e2e`，CI 无 vLLM 时 skip。AC-C-4/AC-C-5 不依赖 vLLM（mock），CI 始终跑。既有 mock 版测试保留。

## 测试文件矩阵

| 测试文件 | 新建/改 | mock/skip | AC 覆盖 | Feature |
|---|---|---|---|---|
| `tests/unit/test_semantic_cache_config.py`（新建） | 新建 | mock embedding（无 vLLM） | AC-A-1, AC-A-2, AC-A-3, AC-A-4, AC-A-5 | F-S-1 |
| `tests/unit/test_ann_search.py`（新建） | 新建 | mock embedding_store + mock hnswlib；AC-B-4 标 marker；hnswlib 未装 skip | AC-B-1, AC-B-2, AC-B-3, AC-B-4, AC-B-5 | F-S-2 |
| `tests/unit/test_related_pages_ann.py`（新建或扩） | 新建/扩 | mock（无 vLLM） | AC-B-5 | F-S-2 |
| `tests/unit/test_embedding_benchmark.py`（扩） | 扩 | AC-C-1 mock embedding（CI 跑）；AC-C-2/3 标 marker skip if no vLLM；AC-C-4 mock 不可达 CI 跑；AC-C-5 mock embedding CI 跑；既有 mock 版保留 | AC-C-1, AC-C-2, AC-C-3, AC-C-4, AC-C-5 | F-S-3 |

## 依赖约束

- `hnswlib`（MIT 许可，`pip install hnswlib`）——新增 pip 依赖，加入 `pyproject.toml` `[semantic]` extra。
- 不引入 faiss/torch/scipy 等重依赖。
- numpy 已是既有依赖（ADR-010），`batch_cosine_similarity` 复用。

## CI 兼容矩阵

| AC | 依赖 vLLM? | 依赖 hnswlib? | CI 行为 | marker |
|---|---|---|---|---|
| AC-A-1..5 | 否（mock embedding） | 否 | CI 始终跑 | 无 |
| AC-B-1/2/3 | 否（mock） | 是（mock hnswlib 或 skip） | CI 跑（mock hnswlib）；hnswlib 未装 skip | `@pytest.mark.skipif` |
| AC-B-4 | 否（mock 向量） | 是 | CI 跑（mock）；hnswlib 未装 skip | `@pytest.mark.skipif` |
| AC-B-5 | 否（mock） | 否（检查路径不执行逐条 SELECT） | CI 始终跑 | 无 |
| AC-C-1 | 否（mock embedding） | 否 | CI 始终跑 | 无 |
| AC-C-2 | 是（真实 vLLM P99） | 是 | CI skip if no vLLM | `@pytest.mark.benchmark_e2e` |
| AC-C-3 | 是（真实 vLLM P99） | 否（合成数据用随机向量） | CI skip if no vLLM | `@pytest.mark.benchmark_e2e` |
| AC-C-4 | 否（mock 不可达） | 否 | CI 始终跑 | 无 |
| AC-C-5 | 否（mock embedding） | 否 | CI 始终跑 | 无 |

## 落地状态（05 实施回填）

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-A-1 | F-S-1 | `test_semantic_cache_config.py::test_ac_a_1_cache_disabled_no_hits` | built ✓ (22d25e6) |
| AC-A-2 | F-S-1 | `test_semantic_cache_config.py::test_ac_a_2_cache_enabled_hits_increase` | built ✓ (22d25e6) |
| AC-A-3 | F-S-1 | `test_semantic_cache_config.py::test_ac_a_3_threshold_skips_cache_write` | built ✓ (22d25e6) |
| AC-A-4 | F-S-1 | `test_semantic_cache_config.py::test_ac_a_4_backward_compatibility` | built ✓ (22d25e6) |
| AC-A-5 | F-S-1 | `test_semantic_cache_config.py::test_ac_a_5_keyword_cache_unaffected` | built ✓ (22d25e6) |
| AC-B-1 | F-S-2 | `test_ann_search.py::test_ac_b_1_ann_auto_switch` | built ✓ (9e456df) |
| AC-B-2 | F-S-2 | `test_ann_search.py::test_ac_b_2_small_scale_cosine` | built ✓ (9e456df) |
| AC-B-3 | F-S-2 | `test_ann_search.py::test_ac_b_3_ann_fallback` | built ✓ (9e456df) |
| AC-B-4 | F-S-2 | `test_ann_search.py::test_ac_b_4_recall_consistency` | built ✓ (9e456df) |
| AC-B-5 | F-S-2 | `test_ann_search.py::test_ac_b_5_related_pages_reuse` + `test_related_pages_ann.py` | built ✓ (9e456df) |
| AC-C-1 | F-S-3 | `test_embedding_benchmark.py::test_ac_c_1_cache_hit_via_stats_mock` | built ✓ (99bc06c) |
| AC-C-2 | F-S-3 | `test_embedding_benchmark.py::test_ac_c_2_ann_vs_cosine` (benchmark_e2e) | built ✓ (99bc06c) |
| AC-C-3 | F-S-3 | `test_embedding_benchmark.py::test_ac_c_3_scale_curve` (benchmark_e2e) | built ✓ (99bc06c) |
| AC-C-4 | F-S-3 | `test_embedding_benchmark.py::test_ac_b_4_vllm_unreachable_exits_without_mock` | built ✓ (pre-existing, kept) |
| AC-C-5 | F-S-3 | `test_embedding_benchmark.py::test_ac_c_1_cache_hit_via_stats_mock` (mock, CI-safe) | built ✓ (99bc06c) |
