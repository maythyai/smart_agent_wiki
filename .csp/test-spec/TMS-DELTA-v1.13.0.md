# TMS Delta — v1.13.0（2026-09-06）

> 03 测试规约 delta。E2E 收尾轮：ingest 目录递归 + 真实 vLLM benchmark + REST 兼容别名+CHANGELOG + coverage 棘轮 67 + 闭合 Q1/Q3 补记。
> 基线：v1.12.0 = 2076 passed / 3 skipped / ruff 0 / coverage 66% / smoke 6/6。
> benchmark 须真实 vLLM 不 mock（CI 无 vLLM 时 marker skip）。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-A-1（目录递归 ingest） | F-R-1 | `tests/unit/test_ingest_directory.py`（新建）：建 tmp dir 含 3 .md → `pipeline.ingest(dir)` → 3 文件全部入库，claim_count ≥ 3，0 "Is a directory" 错误 | mapped |
| AC-A-2（空目录） | F-R-1 | `test_ingest_directory.py`：建 tmp 空目录 → `pipeline.ingest(dir)` → errors 含 "No ingestible files found" + claim_count=0 | mapped |
| AC-A-3（部分失败） | F-R-1 | `test_ingest_directory.py`：建 tmp dir 含 2 .md + 1 损坏 .pdf → 2 .md 成功 + 1 .pdf 记 errors + 不中断 | mapped |
| AC-A-4（子目录递归） | F-R-1 | `test_ingest_directory.py`：建 tmp dir 含子目录，子目录内 1 .md → 子目录文件被 ingest + claim_count 含子目录 | mapped |
| AC-A-5（排除 SAW 内部目录） | F-R-1 | `test_ingest_directory.py`：建 tmp dir 含 `.saw/` 子目录 + `.saw/inside.md` → `.saw/inside.md` 不被 ingest | mapped |
| AC-B-1（真实 API 召回） | F-R-2 | `tests/unit/test_embedding_benchmark.py`（扩，标 `@pytest.mark.benchmark_e2e`，CI 无 vLLM skip）：真 vLLM 可达时跑 `scripts/benchmark_semantic.py` 逻辑 → semantic 召回 ≥ BM25（同义查询集） | mapped |
| AC-B-2（P99 延迟） | F-R-2 | `test_embedding_benchmark.py`（标 marker，skip if no vLLM）：跑 benchmark P99 统计 → 输出 P99 数值，记录 baseline | mapped |
| AC-B-3（cache 命中率） | F-R-2 | `test_embedding_benchmark.py`（标 marker，skip if no vLLM）：同查询跑 2 次 → 第 2 次命中 cache，延迟显著低，输出 hit/miss | mapped |
| AC-B-4（vLLM 不可达报错） | F-R-2 | `test_embedding_benchmark.py`（不依赖 vLLM，CI 始终跑）：mock vLLM 不可达 → benchmark 报 "vLLM endpoint unreachable" 退出，不 mock | mapped |
| AC-C-1（别名兼容） | F-R-3 | `tests/unit/test_workflow_rest_db.py`（扩）：`GET /workflows` 返回非空 → 每个 item 含 `name` 且 == `definition_name` + 含 `workflow` 且 == `definition_name` | mapped |
| AC-C-2（CHANGELOG 存在） | F-R-3 | `tests/unit/test_changelog.py`（新建）：读项目根 `CHANGELOG.md` → 文件存在 + 含 v1.11.0 `/workflows` 行为变更条目 | mapped |
| AC-C-3（CHANGELOG 回溯） | F-R-3 | `test_changelog.py`（扩）：读 `CHANGELOG.md` → 含 v1.12.0 embedding pivot 条目 + v1.13.0 本轮条目 | mapped |
| AC-D-1（fail_under 提升） | F-R-4 | `tests/unit/engines/compile/test_coverage_config.py`（改）：读 pyproject.toml → `fail_under` 值为 67（或 ≥ 65 棘轮） | mapped |
| AC-D-2（实际覆盖率达标） | F-R-4 | CI `pytest --cov` → coverage 报告 ≥ 67% | mapped |
| AC-E-1（Q1 闭合标注） | F-R-5 | `tests/unit/test_retrospective_closure.py`（新建）：读 `retrospective-v1.12.0.md` Q1 → 含 `**v1.13.0 闭合**` + commit `84e1776` | mapped |
| AC-E-2（Q3 闭合标注） | F-R-5 | `test_retrospective_closure.py`（扩）：读 Q3 → 含 `**v1.13.0 闭合**` + ST fallback 已删 | mapped |

## 约定

- **ingest 目录递归测试**（`test_ingest_directory.py`，新建）：建 tmp dir + `.md` 文件 + `.saw/` 子目录，调 `pipeline.ingest(dir)`，断言聚合 IngestResult（claim_count + errors + parser="directory-batch"）。不依赖 LLM（纯 classify+extract+fuse）。单文件回归测试（既有 `test_ingest*.py`）确认单文件路径不回归。
- **benchmark 真实 vLLM 测试**（`test_embedding_benchmark.py`，扩）：AC-B-1/2/3 标 `@pytest.mark.benchmark_e2e`（或检测 vLLM 8001 可达的 `importorskip`/skip 条件），CI 无 vLLM 时 skip（不影响 CI 绿）。AC-B-4 不依赖 vLLM（mock 不可达 health check），CI 始终跑。既有 mock 版 `test_benchmark_semantic_vs_bm25_recall` / `test_benchmark_p99_latency_mock` 保留（验证逻辑路径，CI 跑）。
- **REST 别名测试**（`test_workflow_rest_db.py`，扩）：`GET /workflows` 返回非空列表 → 断言每个 item 含 `name` 且 == `definition_name` + `workflow` 且 == `definition_name`。
- **CHANGELOG 测试**（`test_changelog.py`，新建）：读项目根 `CHANGELOG.md` → 断言文件存在 + 含版本条目（v1.11.0 workflows + v1.12.0 embedding + v1.13.0 ingest/benchmark/coverage）。
- **coverage 测试适配**（`test_coverage_config.py` + `test_coverage_gate.py`，改）：`fail_under == 65` 改为 `>= 65`（棘轮下限）；`50 <= floor <= 65` 改为 `50 <= floor <= 80`（合理 band）。
- **retrospective 闭合测试**（`test_retrospective_closure.py`，新建）：读 `retrospective-v1.12.0.md` → 断言 Q1/Q3 段落含闭合标注。

## 测试文件矩阵

| 测试文件 | 新建/改 | mock/skip | AC 覆盖 | Feature |
|---|---|---|---|---|
| `tests/unit/test_ingest_directory.py`（新建） | 新建 | 无（纯 classify+extract，无 LLM） | AC-A-1, AC-A-2, AC-A-3, AC-A-4, AC-A-5 | F-R-1 |
| `tests/unit/test_embedding_benchmark.py`（扩） | 扩 | AC-B-1/2/3 标 marker skip if no vLLM；AC-B-4 mock 不可达 CI 跑；既有 mock 版保留 | AC-B-1, AC-B-2, AC-B-3, AC-B-4 | F-R-2 |
| `tests/unit/test_workflow_rest_db.py`（扩） | 扩 | 无（in-memory DB） | AC-C-1 | F-R-3 |
| `tests/unit/test_changelog.py`（新建） | 新建 | 无（文件存在性检查） | AC-C-2, AC-C-3 | F-R-3 |
| `tests/unit/engines/compile/test_coverage_config.py`（改） | 改 | 无（读 pyproject.toml） | AC-D-1 | F-R-4 |
| `tests/unit/test_coverage_gate.py`（改） | 改 | 无（读 pyproject.toml + 子进程） | AC-D-1 | F-R-4 |
| `tests/unit/test_retrospective_closure.py`（新建） | 新建 | 无（文件读取） | AC-E-1, AC-E-2 | F-R-5 |

## 落地状态（05 实施回填）

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-A-1 | F-R-1 | `tests/unit/test_ingest_directory.py::test_dir_recursive_ingest`（新建） | mapped |
| AC-A-2 | F-R-1 | `test_ingest_directory.py::test_dir_empty_no_ingestible`（新建） | mapped |
| AC-A-3 | F-R-1 | `test_ingest_directory.py::test_dir_partial_failure`（新建） | mapped |
| AC-A-4 | F-R-1 | `test_ingest_directory.py::test_dir_subdirectory_recursion`（新建） | mapped |
| AC-A-5 | F-R-1 | `test_ingest_directory.py::test_dir_excludes_saw_internal`（新建） | mapped |
| AC-B-1 | F-R-2 | `test_embedding_benchmark.py::test_benchmark_real_api_recall`（扩，marker skip if no vLLM） | mapped |
| AC-B-2 | F-R-2 | `test_embedding_benchmark.py::test_benchmark_real_p99`（扩，marker skip if no vLLM） | mapped |
| AC-B-3 | F-R-2 | `test_embedding_benchmark.py::test_benchmark_real_cache_hit`（扩，marker skip if no vLLM） | mapped |
| AC-B-4 | F-R-2 | `test_embedding_benchmark.py::test_benchmark_vllm_unreachable`（扩，mock 不可达 CI 跑） | mapped |
| AC-C-1 | F-R-3 | `test_workflow_rest_db.py::test_workflows_response_alias`（扩） | mapped |
| AC-C-2 | F-R-3 | `test_changelog.py::test_changelog_exists_v111`（新建） | mapped |
| AC-C-3 | F-R-3 | `test_changelog.py::test_changelog_backtrace_v112_v113`（新建） | mapped |
| AC-D-1 | F-R-4 | `test_coverage_config.py::test_fail_under_is_67`（改）+ `test_coverage_gate.py::test_gate_config`（改） | mapped |
| AC-D-2 | F-R-4 | CI `pytest --cov` ≥ 67% | mapped |
| AC-E-1 | F-R-5 | `test_retrospective_closure.py::test_q1_closed`（新建） | mapped |
| AC-E-2 | F-R-5 | `test_retrospective_closure.py::test_q3_closed`（新建） | mapped |

## v1.13.0 实施落地状态（05-impl done）

**日期**: 2026-09-06
**结果**: 2179 passed, 3 skipped, 2 deselected (benchmark_e2e), ruff 0, coverage 67%, smoke 6/6

### 用例落地状态

| AC | 测试文件 | 用例数 | 状态 |
|---|---|---|---|
| AC-A-1..5 | `tests/unit/test_ingest_directory.py` | 5 | ✅ pass |
| AC-B-1..3 | `tests/unit/test_embedding_benchmark.py` (@benchmark_e2e) | 3 | ✅ pass (vLLM) / skip (CI) |
| AC-B-4 | `tests/unit/test_embedding_benchmark.py` | 1 | ✅ pass (always) |
| AC-C-1 | `tests/unit/test_workflow_rest_db.py` (扩) | 2 | ✅ pass |
| AC-C-2..3 | `tests/unit/test_changelog.py` | 2 | ✅ pass |
| AC-D-1 | `tests/unit/engines/compile/test_coverage_config.py` | 1 | ✅ pass (fail_under=67) |
| AC-D-2 | CI pytest --cov | — | ✅ pass (67% ≥ 67) |
| AC-E-1..2 | `tests/unit/test_retrospective_closure.py` | 2 | ✅ pass |

### 补充覆盖率测试（T-F-R-4）

| 测试文件 | 用例数 | 覆盖模块 | 状态 |
|---|---|---|---|
| `test_linter_coverage.py` | 25 | linter.py (14%→~95%) | ✅ pass |
| `test_code_wiki_coverage.py` | 15 | code_wiki.py (14%→~60%) | ✅ pass |
| `test_concept_graph_coverage.py` | 22 | concept_graph.py (20%→~80%) | ✅ pass |
| `test_archiver_coverage.py` | 12 | archiver.py (19%→~85%) | ✅ pass |
| `test_feedback_coverage.py` | 16 | feedback.py (31%→~85%) | ✅ pass |

总计新增测试：90（5+4+4+75+2）
