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
| F-Q-1 | SPEC-F-Q-1 | T-F-Q-1 | 1 | 53cd582 |
| F-Q-2 | SPEC-F-Q-2 | T-F-Q-2 | 2 | 53cd582 |
| F-Q-3 | SPEC-F-Q-3 | T-F-Q-3 | 2 | 53cd582 |
| F-Q-4 | SPEC-F-Q-4 | T-F-Q-4 | 2 | 53cd582 |

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

## v1.15.0 delta（agent/link 能力）

| PRD 模块(§3) | AC | Feature | Spec |
|---|---|---|---|
| §3.1 F-T-1 | AC-A-1 | F-T-1 | SPEC-F-T-1 |
| §3.1 | AC-A-2 | F-T-1 | SPEC-F-T-1 |
| §3.1 | AC-A-3 | F-T-1 | SPEC-F-T-1 |
| §3.1 | AC-A-4 | F-T-1 | SPEC-F-T-1 |
| §3.2 F-T-2 | AC-B-1 | F-T-2 | SPEC-F-T-2 |
| §3.2 | AC-B-2 | F-T-2 | SPEC-F-T-2 |
| §3.2 | AC-B-3 | F-T-2 | SPEC-F-T-2 |
| §3.2 | AC-B-4 | F-T-2 | SPEC-F-T-2 |
| §3.3 F-T-3 | AC-C-1 | F-T-3 | SPEC-F-T-3 |
| §3.3 | AC-C-2 | F-T-3 | SPEC-F-T-3 |
| §3.3 | AC-C-3 | F-T-3 | SPEC-F-T-3 |
| §3.3 | AC-C-4 | F-T-3 | SPEC-F-T-3 |

### Task 追溯（Feature → Task，[TBD-04 待拆]）

| Feature | Spec | Task | Wave | Commit |
|---|---|---|---|---|
| F-T-1 | SPEC-F-T-1 | T-F-T-1 | 1 | 53cd582 |
| F-T-2 | SPEC-F-T-2 | T-F-T-2 | 1 | 8f6ad2b |
| F-T-3 | SPEC-F-T-3 | T-F-T-3 | 1 | 59f9552 |

链：PRD AC → Feature → Spec → Task，12 AC 全映射。03-tech done，04-tasks 待拆。

## v1.16.0 delta（realtime 仪表盘 v4.3）

| PRD 模块(§3) | AC | Feature | Spec |
|---|---|---|---|
| §3.1 F-U-1 | AC-D-1 | F-U-1 | SPEC-F-U-1 |
| §3.1 | AC-D-2 | F-U-1 | SPEC-F-U-1 |
| §3.1 | AC-D-3 | F-U-1 | SPEC-F-U-1 |
| §3.1 | AC-D-4 | F-U-1 | SPEC-F-U-1 |
| §3.2 F-U-2 | AC-D-5 | F-U-2 | SPEC-F-U-2 |
| §3.2 | AC-D-6 | F-U-2 | SPEC-F-U-2 |
| §3.2 | AC-D-7 | F-U-2 | SPEC-F-U-2 |
| §3.3 F-U-3 | AC-D-8 | F-U-3 | SPEC-F-U-3 |

### Task 追溯（Feature → Task，[TBD-04 待拆]）

| Feature | Spec | Task | Wave | Commit |
|---|---|---|---|---|
| F-U-1 | SPEC-F-U-1 | T-F-U-1 | 1 | c42df02 |
| F-U-2 | SPEC-F-U-2 | T-F-U-2 | 1 | a95e476 |
| F-U-3 | SPEC-F-U-3 | T-F-U-3 | 2 | 0704e5a |

链：PRD AC → Feature → Spec → Task → commit，8 AC 全映射（AC-D-9 系统级 NFR）。05-impl done，vitest 64 passed, build success, backend 2220 passed 不回归。

## v1.17.0 delta（desktop 完成 v4.4）

| PRD 模块(§3) | AC | Feature | Spec |
|---|---|---|---|
| §3.1 F-V-1 | AC-V-1 | F-V-1 | SPEC-F-V-1 |
| §3.1 | AC-V-2 | F-V-1 | SPEC-F-V-1 |
| §3.2 F-V-2 | AC-W-1 | F-V-2 | SPEC-F-V-2 |
| §3.2 | AC-W-2 | F-V-2 | SPEC-F-V-2 |
| §3.3 F-V-3 | AC-B-1 | F-V-3 | SPEC-F-V-3 |
| §3.3 | AC-B-2 | F-V-3 | SPEC-F-V-3 |
| §3.4 F-V-4 | AC-C-1 | F-V-4 | SPEC-F-V-4 |
| §3.4 | AC-C-2 | F-V-4 | SPEC-F-V-4 |
| §3.4 | AC-C-3 | F-V-4 | SPEC-F-V-4 |

### Task 追溯（Feature → Task，[TBD-04 待拆]）

| Feature | Spec | Task | Wave | Commit |
|---|---|---|---|---|
| F-V-1 | SPEC-F-V-1 | T-F-V-1 | 1 | f922a99 |
| F-V-2 | SPEC-F-V-2 | T-F-V-2 | 2 | 19578ef |
| F-V-3 | SPEC-F-V-3 | T-F-V-3 | 2 | 6bb6949 |
| F-V-4 | SPEC-F-V-4 | T-F-V-4 | 2 | 1ca63a1 |

链：PRD AC → Feature → Spec → Task，9 AC 全映射。03-tech done，04-tasks 待拆。

## v1.18.0 delta（per-request workspace 注入 + O4 tag 流程修复）

| PRD 模块(§3) | AC | Feature | Spec |
|---|---|---|---|
| §3.1 F-W-1 | AC-WS-1 | F-W-1 | SPEC-F-W-1 |
| §3.1 | AC-WS-2 | F-W-1 | SPEC-F-W-1 |
| §3.1 | AC-WS-3 | F-W-1 | SPEC-F-W-1 |
| §3.1 | AC-WS-4 | F-W-1 | SPEC-F-W-1 |
| §3.1 | AC-WS-5 | F-W-1 | SPEC-F-W-1 |
| §3.2 F-W-2 | AC-O4-1 | F-W-2 | SPEC-F-W-2 |
| §3.2 | AC-O4-2 | F-W-2 | SPEC-F-W-2 |

### Task 追溯（Feature → Task，[TBD-04 待拆]）

| Feature | Spec | Task | Wave | Commit |
|---|---|---|---|---|
| F-W-1 | SPEC-F-W-1 | T-F-W-1 | 1 | [TBD] |
| F-W-2 | SPEC-F-W-2 | T-F-W-2 | 1 | [TBD] |

链：PRD AC → Feature → Spec → Task，7 AC 全映射。03-tech done，04-tasks 待拆。
