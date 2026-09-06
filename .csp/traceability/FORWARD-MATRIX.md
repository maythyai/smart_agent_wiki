# Forward Matrix — PRD → Feature → Spec

> 正向追溯：PRD 模块/AC → decomposition Feature → Spec。PRD `product-hardening-v1`。

| PRD 模块(§3) | AC | Feature | Spec |
|---|---|---|---|
| §3.1 e2e-usability | AC-E2E-1 | F-A-1, F-A-6 | SPEC-F-A-1, SPEC-F-A-6 |
| §3.1 | AC-E2E-2 | F-A-5 | SPEC-F-A-5 |
| §3.1 | (链路) | F-A-2, F-A-3, F-A-4 | SPEC-F-A-2/3/4 |
| §3.2 claim-alignment | AC-ALIGN-1 | F-B-1 | SPEC-F-B-1 |
| §3.2 | AC-ALIGN-2 | F-B-2, F-B-3 | SPEC-F-B-2/3 |
| §3.3 security | AC-SEC-1 | F-C-1 | SPEC-F-C-1 |
| §3.3 | AC-SEC-2 | F-C-2 | SPEC-F-C-2 |
| §3.3 | AC-SEC-3 | F-C-3 | SPEC-F-C-3 |
| §3.3 | (守卫/token) | F-C-4, F-C-5 | SPEC-F-C-4/5 |
| §3.4 observability | AC-OBS-1 | F-D-1, F-D-2 | SPEC-F-D-1/2 |
| §3.4 | AC-OBS-2 | F-D-3 | SPEC-F-D-3 |
| §3.5 test-gate | AC-TEST-1 | F-E-2 | SPEC-F-E-2 |
| §3.5 | AC-TEST-2 | F-A-6, F-E-3 | SPEC-F-A-6, SPEC-F-E-3 |
| §3.5 | (基线) | F-E-1 | SPEC-F-E-1 |

## 粒度
PRD feature_count=5（模块）→ decomposition 5 域 → 20 原子 Feature → 20 Spec（1:1）。模块↔域 1:1，域↔Feature 1:N，Feature↔Spec 1:1。

## Task 追溯（Feature → Task）
| Feature | Spec | Task | Wave |
|---|---|---|---|
| F-A-1 | SPEC-F-A-1 | T-F-A-1-1 | 1 |
| F-A-2 | SPEC-F-A-2 | T-F-A-2-1 | 2 |
| F-A-3 | SPEC-F-A-3 | T-F-A-3-1 | 2 |
| F-A-4 | SPEC-F-A-4 | T-F-A-4-1 | 2 |
| F-A-5 | SPEC-F-A-5 | T-F-A-5-1 | 3 |
| F-A-6 | SPEC-F-A-6 | T-F-A-6-1 | 3 |
| F-B-1 | SPEC-F-B-1 | T-F-B-1-1 | 1 |
| F-B-2 | SPEC-F-B-2 | T-F-B-2-1 | 2 |
| F-B-3 | SPEC-F-B-3 | T-F-B-3-1 | 2 |
| F-C-1 | SPEC-F-C-1 | T-F-C-1-1 | 1 |
| F-C-2 | SPEC-F-C-2 | T-F-C-2-1 | 1 |
| F-C-3 | SPEC-F-C-3 | T-F-C-3-1 | 1 |
| F-C-4 | SPEC-F-C-4 | T-F-C-4-1 | 1 |
| F-C-5 | SPEC-F-C-5 | T-F-C-5-1 | 1 |
| F-D-1 | SPEC-F-D-1 | T-F-D-1-1 | 1 |
| F-D-2 | SPEC-F-D-2 | T-F-D-2-1 | 2 |
| F-D-3 | SPEC-F-D-3 | T-F-D-3-1 | 1 |
| F-E-1 | SPEC-F-E-1 | T-F-E-1-1 | 1 |
| F-E-2 | SPEC-F-E-2 | T-F-E-2-1 | 2 |
| F-E-3 | SPEC-F-E-3 | T-F-E-3-1 | 3 |

链：PRD AC → Feature → Spec → Task，全 20 闭环。

## 05 实施进度（commit 续写）
| Task | status | commit |
|---|---|---|
| T-F-C-4-1 | done | fece73d |
| T-F-C-3-1 | done | cf5b86b |
| T-F-B-1-1 | done | 622859c |
| T-F-A-1-1 | done | d92ece0 |
| T-F-E-1-1 | deferred | — |

链 PRD AC → Feature → Spec → Task → commit 续写；本切片覆盖 AC-SEC-1(URL guard)/AC-SEC-3(限流)/AC-ALIGN-1(宣称diff)/AC-E2E-1(冒烟骨架 partial)。

## v1.10.0 delta（embedding 语义搜索）

| PRD 模块(§3) | AC | Feature | Spec |
|---|---|---|---|
| §3.1 F-EMB-1 | AC-EMB-1 | F-N-1 | SPEC-F-N-1 |
| §3.1 | AC-EMB-2 | F-N-1 | SPEC-F-N-1 |
| §3.1 | AC-EMB-3 | F-N-1 | SPEC-F-N-1 |
| §3.2 F-EMB-2 | AC-SEM-1 | F-N-2 | SPEC-F-N-2 |
| §3.2 | AC-SEM-2 | F-N-2 | SPEC-F-N-2 |
| §3.2 | AC-SEM-3 | F-N-2 | SPEC-F-N-2 |
| §3.3 F-EMB-3 | AC-LINK-1 | F-N-3 | SPEC-F-N-3 |
| §3.3 | AC-LINK-2 | F-N-3 | SPEC-F-N-3 |
| §3.3 | AC-LINK-3 | F-N-3 | SPEC-F-N-3 |
| §3.4 F-EMB-4 | AC-TEST-1 | F-N-4 | SPEC-F-N-4 |
| §3.4 | AC-TEST-2 | F-N-4 | SPEC-F-N-4 |
| §3.4 | AC-TEST-3 | F-N-4 | SPEC-F-N-4 |

### Task 追溯（Feature → Task，[TBD-04 待拆]）

| Feature | Spec | Task | Wave | Commit |
|---|---|---|---|---|
| F-N-1 | SPEC-F-N-1 | T-F-N-1 | 1 | ecbdb75 |
| F-N-2 | SPEC-F-N-2 | T-F-N-2 | 2 | 9660ecc |
| F-N-3 | SPEC-F-N-3 | T-F-N-3 | 2 | 3b2039e |
| F-N-4 | SPEC-F-N-4 | T-F-N-4 | 2 | e7fb6c6 |

链：PRD AC → Feature → Spec → Task → commit，12 AC 全闭环。05-impl done.

## v1.11.0 delta（债务收口 IV / bug fix）

| PRD 模块(§3) | AC | Feature | Spec |
|---|---|---|---|
| §3.1 F-O-1 (N7) | AC-CACHE-1 | F-O-1 | SPEC-F-O-1 |
| §3.1 | AC-CACHE-2 | F-O-1 | SPEC-F-O-1 |
| §3.1 | AC-CACHE-3 | F-O-1 | SPEC-F-O-1 |
| §3.1 | AC-CACHE-4 | F-O-1 | SPEC-F-O-1 |
| §3.2 F-O-2 (N2/K1) | AC-COV-1 | F-O-2 | SPEC-F-O-2 |
| §3.2 | AC-COV-2 | F-O-2 | SPEC-F-O-2 |
| §3.3 F-O-3 (M3) | AC-WF-1 | F-O-3 | SPEC-F-O-3 |
| §3.3 | AC-WF-2 | F-O-3 | SPEC-F-O-3 |
| §3.3 | AC-WF-3 | F-O-3 | SPEC-F-O-3 |
| §3.4 F-O-4 (N5) | AC-SPEC-1 | F-O-4 | SPEC-F-O-4 |
| §3.4 | AC-SPEC-2 | F-O-4 | SPEC-F-O-4 |
| §3.5 F-O-4 (N6) | AC-HASH-1 | F-O-4 | SPEC-F-O-4 |

### Task 追溯（Feature → Task，05 实施完成）

| Feature | Spec | Task | Wave | Commit |
|---|---|---|---|---|
| F-O-1 | SPEC-F-O-1 | T-F-O-1 | 1 | 209c294 |
| F-O-2 | SPEC-F-O-2 | T-F-O-2 | 1 | 42b9399 |
| F-O-3 | SPEC-F-O-3 | T-F-O-3 | 1 | e3869d3 |
| F-O-4 | SPEC-F-O-4 | T-F-O-4 | 1 | 0f0e82e |

链：PRD AC → Feature → Spec → Task → commit，12 AC 全闭环。05-impl done.

## v1.12.0 delta（embedding API 重构）

| PRD 模块(§3) | AC | Feature | Spec |
|---|---|---|---|
| §3.1 F-EA-1 | AC-EA-1 | F-Q-1 | SPEC-F-Q-1 |
| §3.1 | AC-EA-2 | F-Q-1 | SPEC-F-Q-1 |
| §3.2 F-EA-2 | AC-DIM-1 | F-Q-2 | SPEC-F-Q-2 |
| §3.2 | AC-DIM-2 | F-Q-2 | SPEC-F-Q-2 |
| §3.3 F-EA-3 | AC-FB-1 | F-Q-3 | SPEC-F-Q-3 |
| §3.3 | AC-FB-2 | F-Q-3 | SPEC-F-Q-3 |
| §3.4 F-EA-4 | AC-TEST-1 | F-Q-4 | SPEC-F-Q-4 |
| §3.4 | AC-TEST-2 | F-Q-4 | SPEC-F-Q-4 |
| §3.4 | AC-TEST-3 | F-Q-4 | SPEC-F-Q-4 |

### Task 追溯（Feature → Task，[TBD-04 待拆]）

| Feature | Spec | Task | Wave | Commit |
|---|---|---|---|---|
| F-Q-1 | SPEC-F-Q-1 | T-F-Q-1 | 1 | [TBD-05] |
| F-Q-2 | SPEC-F-Q-2 | T-F-Q-2 | 2 | [TBD-05] |
| F-Q-3 | SPEC-F-Q-3 | T-F-Q-3 | 2 | [TBD-05] |
| F-Q-4 | SPEC-F-Q-4 | T-F-Q-4 | 2 | [TBD-05] |

链：PRD AC → Feature → Spec → Task，9 AC 全映射。03-tech done，04-tasks 待拆。

### v1.12.0 — embedding API pivot

| PRD Item | Feature | Spec | Task | Commit | AC | Test |
|---|---|---|---|---|---|---|
| PRD-EA-1 | F-Q-1 | SPEC-F-Q-1 | T-F-Q-1 | f4f4869 | AC-EA-1, AC-EA-2 | test_embedding_index (4), test_embedding_degradation (4) |
| PRD-EA-2 | F-Q-2 | SPEC-F-Q-2 | T-F-Q-2 | f4e9f04 | AC-DIM-1, AC-DIM-2 | test_embedding_index::test_dim_change_triggers_rebuild, test_emb_ac1 (model 列) |
| PRD-EA-3 | F-Q-3 | SPEC-F-Q-3 | T-F-Q-3 | 4818926 | AC-FB-1, AC-FB-2 | test_semantic_search::test_sem_fb1_st_fallback, test_sem_fb2_no_st_api |
| PRD-EA-4 | F-Q-4 | SPEC-F-Q-4 | T-F-Q-4 | 65f036f | AC-TEST-1, AC-TEST-2, AC-TEST-3 | test_embedding_index/semantic/related (no importorskip), test_ci_workflow::test_embedding_tests_no_importorskip, test_embedding_benchmark |

### v1.13.0 — E2E 收尾轮

| PRD Item | Feature | Spec | Task | Commit | AC | Test |
|---|---|---|---|---|---|---|
| PRD-R-1 | F-R-1 | SPEC-F-R-1 | T-F-R-1 | 0669d98 | AC-A-1..5 | test_ingest_directory (5) |
| PRD-R-2 | F-R-2 | SPEC-F-R-2 | T-F-R-2 | dc6d299 | AC-B-1..4 | test_embedding_benchmark (4, @benchmark_e2e) |
| PRD-R-3 | F-R-3 | SPEC-F-R-3 | T-F-R-3 | 3284262 | AC-C-1..3 | test_workflow_rest_db (2), test_changelog (2) |
| PRD-R-4 | F-R-4 | SPEC-F-R-4 | T-F-R-4 | 8d9ccca+218c398 | AC-D-1..2 | test_coverage_config (1), test_coverage_gate (1), coverage 67% |
| PRD-R-5 | F-R-5 | SPEC-F-R-5 | T-F-R-5 | 895c8bf | AC-E-1..2 | test_retrospective_closure (2) |

链：PRD AC → Feature → Spec → Task → Commit → Test，16 AC 全映射。

## v1.14.0 delta（semantic 性能优化）

| PRD 模块(§3) | AC | Feature | Spec |
|---|---|---|---|
| §3.1 F-S-1 | AC-A-1 | F-S-1 | SPEC-F-S-1 |
| §3.1 | AC-A-2 | F-S-1 | SPEC-F-S-1 |
| §3.1 | AC-A-3 | F-S-1 | SPEC-F-S-1 |
| §3.1 | AC-A-4 | F-S-1 | SPEC-F-S-1 |
| §3.1 | AC-A-5 | F-S-1 | SPEC-F-S-1 |
| §3.2 F-S-2 | AC-B-1 | F-S-2 | SPEC-F-S-2 |
| §3.2 | AC-B-2 | F-S-2 | SPEC-F-S-2 |
| §3.2 | AC-B-3 | F-S-2 | SPEC-F-S-2 |
| §3.2 | AC-B-4 | F-S-2 | SPEC-F-S-2 |
| §3.2 | AC-B-5 | F-S-2 | SPEC-F-S-2 |
| §3.3 F-S-3 | AC-C-1 | F-S-3 | SPEC-F-S-3 |
| §3.3 | AC-C-2 | F-S-3 | SPEC-F-S-3 |
| §3.3 | AC-C-3 | F-S-3 | SPEC-F-S-3 |
| §3.3 | AC-C-4 | F-S-3 | SPEC-F-S-3 |
| §3.3 | AC-C-5 | F-S-3 | SPEC-F-S-3 |

### Task 追溯（Feature → Task，[TBD-04 待拆]）

| Feature | Spec | Task | Wave | Commit |
|---|---|---|---|---|
| F-S-1 | SPEC-F-S-1 | T-F-S-1 | 1 | 22d25e6 |
| F-S-2 | SPEC-F-S-2 | T-F-S-2 | 1 | 9e456df |
| F-S-3 | SPEC-F-S-3 | T-F-S-3 | 2 | 99bc06c |

链：PRD AC → Feature → Spec → Task，15 AC 全映射。05-impl done (3 commits, 2192 passed, ruff 0, coverage 67.34%, smoke 11/11, hnswlib no torch).
