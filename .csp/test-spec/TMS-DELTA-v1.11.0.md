# TMS Delta — v1.11.0（2026-09-05）

> 03 测试规约 delta。债务收口 IV / bug fix。增量用例。
> 基线：v1.10.0 = 1993 passed / 6 skipped / ruff 0 / coverage 64.2% / smoke 6/6。
> 本轮不依赖 `[learn]` SDK（compiler 测试无 embedding；cache 测试用 mock；workflow REST 用 in-memory DB）。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-CACHE-1（semantic cache 命中） | F-O-1 | `tests/unit/test_semantic_cache.py`（新建，mock）：mock `embed_texts` + `cosine_similarity`，首次 `_semantic_search` → embed/cosine 被调用 → 再次同查询 → embed/cosine **不**被调用（cache 命中）+ 结果一致 | [TBD-impl] |
| AC-CACHE-2（semantic cache workspace 隔离） | F-O-1 | `tests/unit/test_semantic_cache.py`（扩）：workspace A 缓存后，workspace B 同查询 → cache miss（独立计算）+ 不泄漏 A 结果 | [TBD-impl] |
| AC-CACHE-3（semantic cache 索引变更失效） | F-O-1 | `tests/unit/test_semantic_cache.py`（扩）：缓存后 → `get_cache().clear()` → 再次查询 → cache miss（embed/cosine 再被调用） | [TBD-impl] |
| AC-CACHE-4（semantic fallback 不缓存） | F-O-1 | `tests/unit/test_semantic_cache.py`（扩）：mock `embeddings_available()=False` → `_semantic_search` 返回 `semantic_fallback=True` → 检查 cache 无 semantic key（`cache.stats().size` 未增） | [TBD-impl] |
| AC-COV-1（compile/compiler 深覆盖） | F-O-2 | `tests/unit/engines/compile/test_*.py`（新建 7 文件 + conftest，20 用例）：覆盖 compiler.py 30+ 函数 → compiler.py 覆盖率 17%→[TBD] + 全量 coverage ≥65% | [TBD-impl] |
| AC-COV-2（fail_under 棘轮） | F-O-2 | `tests/unit/engines/compile/test_coverage_config.py`：读 `pyproject.toml` `[tool.coverage.report] fail_under` → =65 | [TBD-impl] |
| AC-WF-1（REST 读 DB） | F-O-3 | `tests/unit/test_workflow_rest_db.py`（新建）：in-memory DB + apply_migrations + seed 3 `workflow_executions` → `GET /api/v1/workflows` → 返回 ≥3 条 + 字段含 `workflow_id`/`status`/`steps_completed` | [TBD-impl] |
| AC-WF-2（REST merge live） | F-O-3 | `tests/unit/test_workflow_rest_db.py`（扩）：in-memory `_workflows` 有 1 running（DB 无记录）→ `GET /api/v1/workflows` → 返回含 live running workflow | [TBD-impl] |
| AC-WF-3（CLI/REST 语义一致） | F-O-3 | `tests/unit/test_workflow_rest_db.py`（扩）：同 DB → 对比 CLI `list_recent` SQL 与 REST `list_workflows` SQL → 同表同查询 | [TBD-impl] |
| AC-SPEC-1（Spec 命名回更） | F-O-4 | `tests/unit/test_spec_naming.py`（新建）：grep `saw search rebuild-embeddings` 于 `.csp/specs/SPEC-F-N-1.md` → 0 匹配 | [TBD-impl] |
| AC-SPEC-2（实现不变） | F-O-4 | `tests/unit/test_spec_naming.py`（扩）：`subprocess.run(["saw", "rebuild-embeddings", "--help"])` → exit 0 | [TBD-impl] |
| AC-HASH-1（hash 三处一致） | F-O-4 | `tests/unit/test_hash_consistency.py`（新建）：`git rev-list -n1 v1.10.0` short → 对比 ROADMAP + lifecycle-state.json → 三处一致 | [TBD-impl] |

## 约定

- **cache 测试**（`test_semantic_cache.py`）：用 `unittest.mock.patch` mock `embed_texts` / `cosine_similarity` / `embeddings_available`，不依赖 sentence_transformers，CI 可跑。
- **compile 测试**（`tests/unit/engines/compile/`）：用 `tmp_path` fixture + mock LLM（`_llm_synthesize`），不依赖外部服务。新建目录 `tests/unit/engines/compile/` + `__init__.py` + `conftest.py`。
- **workflow REST 测试**（`test_workflow_rest_db.py`）：用 in-memory SQLite DB + `apply_migrations` + FastAPI `TestClient`，不依赖外部服务。
- **Spec 命名测试**（`test_spec_naming.py`）：纯文件 grep + subprocess `--help`，CI 可跑。
- **hash 一致性测试**（`test_hash_consistency.py`）：`subprocess.run(["git", "rev-list", "-n1", "v1.10.0"])` + 文件读，CI 有 git 可跑。

## 测试文件矩阵

| 测试文件 | mock/importorskip | AC 覆盖 | Feature |
|---|---|---|---|
| `tests/unit/test_semantic_cache.py` | mock（无 SDK） | AC-CACHE-1/2/3/4 | F-O-1 |
| `tests/unit/engines/compile/__init__.py` | — | — | F-O-2 |
| `tests/unit/engines/compile/conftest.py` | — | — | F-O-2 |
| `tests/unit/engines/compile/test_compiler_init.py` | mock LLM | AC-COV-1 | F-O-2 |
| `tests/unit/engines/compile/test_compiler_compile.py` | mock LLM | AC-COV-1 | F-O-2 |
| `tests/unit/engines/compile/test_compiler_helpers.py` | — | AC-COV-1 | F-O-2 |
| `tests/unit/engines/compile/test_compiler_content.py` | mock LLM | AC-COV-1 | F-O-2 |
| `tests/unit/engines/compile/test_compiler_index.py` | — | AC-COV-1 | F-O-2 |
| `tests/unit/engines/compile/test_compiler_cascade.py` | — | AC-COV-1 | F-O-2 |
| `tests/unit/engines/compile/test_coverage_config.py` | — | AC-COV-2 | F-O-2 |
| `tests/unit/test_workflow_rest_db.py` | — | AC-WF-1/2/3 | F-O-3 |
| `tests/unit/test_spec_naming.py` | — | AC-SPEC-1/2 | F-O-4 |
| `tests/unit/test_hash_consistency.py` | — | AC-HASH-1 | F-O-4 |

## 落地状态（05 实施回填，[TBD-impl]）

全部 12 AC 新建测试用例，状态如下（05 实施完成，2026-09-05）：

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-CACHE-1 | F-O-1 | `tests/unit/test_semantic_cache.py::test_ac_cache_1_cache_hit_skips_embed` | ✅ passed |
| AC-CACHE-2 | F-O-1 | `tests/unit/test_semantic_cache.py::test_ac_cache_2_workspace_isolation` | ✅ passed |
| AC-CACHE-3 | F-O-1 | `tests/unit/test_semantic_cache.py::test_ac_cache_3_invalidation_on_clear` | ✅ passed |
| AC-CACHE-4 | F-O-1 | `tests/unit/test_semantic_cache.py::test_ac_cache_4_fallback_not_cached` | ✅ passed |
| AC-COV-1 | F-O-2 | `tests/unit/engines/compile/test_*.py`（7 文件 + conftest，58 用例） | ✅ passed (compiler.py 17%→~70%+) |
| AC-COV-2 | F-O-2 | `tests/unit/engines/compile/test_coverage_config.py::test_fail_under_is_65` | ✅ passed (fail_under=65) |
| AC-WF-1 | F-O-3 | `tests/unit/test_workflow_rest_db.py::test_ac_wf_1_rest_reads_db` | ✅ passed |
| AC-WF-2 | F-O-3 | `tests/unit/test_workflow_rest_db.py::test_ac_wf_2_rest_merges_live` + `test_ac_wf_2_live_overrides_stale_db` | ✅ passed |
| AC-WF-3 | F-O-3 | `tests/unit/test_workflow_rest_db.py::test_ac_wf_3_same_sql_as_cli` | ✅ passed |
| AC-SPEC-1 | F-O-4 | `tests/unit/test_spec_naming.py::test_ac_spec_1_no_stale_command_name` | ✅ passed |
| AC-SPEC-2 | F-O-4 | `tests/unit/test_spec_naming.py::test_ac_spec_2_rebuild_command_registered` | ✅ passed |
| AC-HASH-1 | F-O-4 | `tests/unit/test_hash_consistency.py::test_ac_hash_1_tag_hash_consistent` | ✅ passed |

全部 12 AC 落地，2064 passed / 6 skipped / ruff 0 / coverage 65.36% / smoke 6/6。
