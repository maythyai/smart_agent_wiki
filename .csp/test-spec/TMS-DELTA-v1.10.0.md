# TMS Delta — v1.10.0（2026-09-04）

> 03 测试规约 delta。embedding 语义搜索新能力。增量用例。
> importorskip 范式参照 `tests/unit/engines/learn/test_fsrs.py:15`（`pytest.importorskip("fsrs")`）。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-EMB-1（embedding 索引随 ingest 写入） | F-N-1 | `tests/unit/test_embedding_index.py`（新建）：importorskip + in-memory DB + seed claim → ingest → `SELECT FROM embedding_store` 有行 + dim=384 + workspace_id 正确 | [TBD-impl] |
| AC-EMB-2（无 [learn] 时不报错） | F-N-1 | `tests/unit/test_embedding_degradation.py`（新建，无 importorskip）：mock `embeddings_available()=False` → ingest → claim 正常写入 FTS5 + embedding_store 无行 + 无异常 | [TBD-impl] |
| AC-EMB-3（存量重建索引） | F-N-1 | `tests/unit/test_embedding_index.py`（扩）：seed 3 claims（1 deleted）→ `rebuild-embeddings` → 2 行（deleted skip）+ dim=384 | [TBD-impl] |
| AC-SEM-1（语义检索返回同义结果） | F-N-2 | `tests/unit/test_semantic_search.py`（新建）：importorskip + seed claim "ML" → search "machine learning" --mode semantic → 返回含 "ML" + score>0 + mode=semantic + 降序 | [TBD-impl] |
| AC-SEM-2（无 [learn] 降级 BM25） | F-N-2 | `tests/unit/test_embedding_degradation.py`（扩）：mock `embeddings_available()=False` → search --mode semantic → BM25 结果 + meta.semantic_fallback=true + exit 0 | [TBD-impl] |
| AC-SEM-3（空索引优雅处理） | F-N-2 | `tests/unit/test_semantic_search.py`（扩）：空 DB → search --mode semantic → 空结果 + meta.index_empty=true + exit 0 | [TBD-impl] |
| AC-LINK-1（suggest 含语义相似页面） | F-N-3 | `tests/unit/test_related_pages_embedding.py`（新建）：importorskip + seed 2 pages 无共享 tag/link 但语义相似 → suggest → 相似页面出现 + reasons 含 "semantic similarity" | [TBD-impl] |
| AC-LINK-2（无 [learn] 保持 3-signal） | F-N-3 | `tests/unit/test_embedding_degradation.py`（扩）：mock → suggest → 3-signal 行为不变 + 无 embedding reason + 无异常 | [TBD-impl] |
| AC-LINK-3（语义不相似排名下降） | F-N-3 | `tests/unit/test_related_pages_embedding.py`（扩）：seed 3 pages（A=爬虫+tag python, B=Web框架+tag python, C=爬虫+tag python）→ suggest A → C 排名高于 B | [TBD-impl] |
| AC-TEST-1（CI skip embedding 测试） | F-N-4 | `tests/unit/test_embedding_index.py`（含 importorskip）：CI 无 sentence_transformers → skip 不 fail | [TBD-impl] |
| AC-TEST-2（本地 embedding 测试 pass） | F-N-4 | `tests/unit/test_embedding_index.py`：本地有 [learn] → pass | [TBD-impl] |
| AC-TEST-3（coverage 不回归） | F-N-4 | `tests/unit/test_ci_workflow.py`（扩）：验证 embedding 测试文件 importorskip 覆盖 + coverage ≥ 既有基线 | [TBD-impl] |

## 约定

- importorskip 文件：`test_embedding_index.py` / `test_semantic_search.py` / `test_related_pages_embedding.py` → 首行 `pytest.importorskip("sentence_transformers")`。
- 降级测试文件：`test_embedding_degradation.py`（无 importorskip）→ 用 `unittest.mock.patch` 模拟 `embeddings_available()=False`，测试 AC-EMB-2 / AC-SEM-2 / AC-LINK-2 降级行为。
- CI workflow 检测：`test_ci_workflow.py:62-70` 扩展，验证 embedding 测试文件 importorskip 覆盖。
- 无 ADR-级别测试变更（复用 importorskip 先例）。

## 测试文件矩阵

| 测试文件 | importorskip | AC 覆盖 | Feature |
|---|---|---|---|
| `tests/unit/test_embedding_index.py` | 是 (`sentence_transformers`) | AC-EMB-1, AC-EMB-3, AC-TEST-1, AC-TEST-2 | F-N-1, F-N-4 |
| `tests/unit/test_semantic_search.py` | 是 (`sentence_transformers`) | AC-SEM-1, AC-SEM-3 | F-N-2 |
| `tests/unit/test_related_pages_embedding.py` | 是 (`sentence_transformers`) | AC-LINK-1, AC-LINK-3 | F-N-3 |
| `tests/unit/test_embedding_degradation.py` | 否（mock） | AC-EMB-2, AC-SEM-2, AC-LINK-2 | F-N-1, F-N-2, F-N-3 |
| `tests/unit/test_ci_workflow.py`（扩） | 否 | AC-TEST-3 | F-N-4 |

---

## 落地状态（05 实施回填，2026-09-04）

| AC | 测试文件 | 状态 | 说明 |
|---|---|---|---|
| AC-EMB-1 | `tests/unit/test_embedding_index.py::test_emb_ac1_ingest_writes_embedding` | skip（无 SDK） | importorskip sentence_transformers；须用户装 [learn] 后验证 |
| AC-EMB-2 | `tests/unit/test_embedding_degradation.py::test_emb_ac2_no_learn_no_error` | **pass** | mock embeddings_available()=False，CI 无需 SDK |
| AC-EMB-3 | `tests/unit/test_embedding_index.py::test_emb_ac3_rebuild_skips_deleted` | skip（无 SDK） | importorskip；须用户装 [learn] 后验证 |
| AC-SEM-1 | `tests/unit/test_semantic_search.py::test_sem_ac1_returns_semantic_results` | skip（无 SDK） | importorskip；须用户装 [learn] 后验证 |
| AC-SEM-2 | `tests/unit/test_embedding_degradation.py::test_sem_ac2_degrades_to_bm25` | **pass** | mock，CI 无需 SDK |
| AC-SEM-3 | `tests/unit/test_semantic_search.py::test_sem_ac3_empty_index` | skip（无 SDK） | importorskip；须用户装 [learn] 后验证 |
| AC-LINK-1 | `tests/unit/test_related_pages_embedding.py::test_link_ac1_semantic_suggestion` | skip（无 SDK） | importorskip；须用户装 [learn] 后验证 |
| AC-LINK-2 | `tests/unit/test_embedding_degradation.py::test_link_ac2_no_learn_keeps_3signal` | **pass** | mock，CI 无需 SDK |
| AC-LINK-3 | `tests/unit/test_related_pages_embedding.py::test_link_ac3_dissimilar_ranks_lower` | skip（无 SDK） | importorskip；须用户装 [learn] 后验证 |
| AC-TEST-1 | `tests/unit/test_embedding_index.py` 含 importorskip | **pass** | CI skip 不 fail |
| AC-TEST-2 | `tests/unit/test_embedding_index.py` 本地 pass | skip（无 SDK） | 须用户装 [learn] 后验证 |
| AC-TEST-3 | `tests/unit/test_ci_workflow.py::test_embedding_tests_importorskip` + `test_embedding_degradation_uses_mock_not_importorskip` | **pass** | 验证 importorskip + mock 策略 |

**诚实标注**：sentence_transformers 未装。3 个 importorskip 测试文件（7 测试）自动 skip。
降级测试文件（4 测试）用 mock 通过。实际 embedding E2E 须用户装 `[learn]` extra 后验证。
