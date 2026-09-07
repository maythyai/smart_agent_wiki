# Backward Matrix — Spec → Feature → PRD

> 反向追溯：Spec → Feature → PRD 模块/AC。便于变更影响分析（改某 Spec → 找上游 PRD/Feature）。

| Spec | Feature | PRD 模块 | AC | PMS | CMS ref |
|---|---|---|---|---|---|
| SPEC-F-A-1 | F-A-1 | §3.1 | AC-E2E-1 | e2e-usability | CODE-MODULE-SPEC |
| SPEC-F-A-2 | F-A-2 | §3.1 | (链路) | e2e-usability | CODE-MODULE-SPEC |
| SPEC-F-A-3 | F-A-3 | §3.1 | (链路) | e2e-usability | CODE-MODULE-SPEC |
| SPEC-F-A-4 | F-A-4 | §3.1 | (链路) | e2e-usability | CODE-MODULE-SPEC |
| SPEC-F-A-5 | F-A-5 | §3.1 | AC-E2E-2 | e2e-usability | CODE-MODULE-SPEC |
| SPEC-F-A-6 | F-A-6 | §3.1 | AC-E2E-1, AC-TEST-2 | e2e-usability | CODE-MODULE-SPEC |
| SPEC-F-B-1 | F-B-1 | §3.2 | AC-ALIGN-1 | claim-alignment | entry-points.jsonl |
| SPEC-F-B-2 | F-B-2 | §3.2 | AC-ALIGN-2 | claim-alignment | entry-points.jsonl |
| SPEC-F-B-3 | F-B-3 | §3.2 | (历史标注) | claim-alignment | CODE-MODULE-SPEC |
| SPEC-F-C-1 | F-C-1 | §3.3 | AC-SEC-1 | security-hardening | CODE-MODULE-SPEC |
| SPEC-F-C-2 | F-C-2 | §3.3 | AC-SEC-2 | security-hardening | CODE-MODULE-SPEC |
| SPEC-F-C-3 | F-C-3 | §3.3 | AC-SEC-3 | security-hardening | CODE-MODULE-SPEC |
| SPEC-F-C-4 | F-C-4 | §3.3 | (守卫) | security-hardening | CODE-MODULE-SPEC |
| SPEC-F-C-5 | F-C-5 | §3.3 | (token) | security-hardening | CODE-MODULE-SPEC |
| SPEC-F-D-1 | F-D-1 | §3.4 | AC-OBS-1 | observability | CODE-MODULE-SPEC |
| SPEC-F-D-2 | F-D-2 | §3.4 | AC-OBS-1 | observability | CODE-MODULE-SPEC |
| SPEC-F-D-3 | F-D-3 | §3.4 | AC-OBS-2 | observability | CODE-MODULE-SPEC |
| SPEC-F-E-1 | F-E-1 | §3.5 | (基线) | test-gate | [无] |
| SPEC-F-E-2 | F-E-2 | §3.5 | AC-TEST-1 | test-gate | [无] |
| SPEC-F-E-3 | F-E-3 | §3.5 | AC-TEST-2 | test-gate | [无] |

## v1.10.0 delta（embedding 语义搜索）

| Spec | Feature | PRD 模块 | AC | PMS | CMS ref | Commit |
|---|---|---|---|---|---|---|
| SPEC-F-N-1 | F-N-1 | §3.1 | AC-EMB-1/2/3 | embedding | CODE-MODULE-SPEC | ecbdb75 |
| SPEC-F-N-2 | F-N-2 | §3.2 | AC-SEM-1/2/3 | embedding | CODE-MODULE-SPEC | 9660ecc |
| SPEC-F-N-3 | F-N-3 | §3.3 | AC-LINK-1/2/3 | embedding | CODE-MODULE-SPEC | 3b2039e |
| SPEC-F-N-4 | F-N-4 | §3.4 | AC-TEST-1/2/3 | embedding | [无] | e7fb6c6 |

## v1.11.0 delta（债务收口 IV / bug fix）

| Spec | Feature | PRD 模块 | AC | PMS | CMS ref | Commit |
|---|---|---|---|---|---|---|
| SPEC-F-O-1 | F-O-1 | §3.1 | AC-CACHE-1/2/3/4 | debt-closure | CODE-MODULE-SPEC | 209c294 |
| SPEC-F-O-2 | F-O-2 | §3.2 | AC-COV-1/2 | debt-closure | CODE-MODULE-SPEC | 42b9399 |
| SPEC-F-O-3 | F-O-3 | §3.3 | AC-WF-1/2/3 | debt-closure | CODE-MODULE-SPEC | e3869d3 |
| SPEC-F-O-4 | F-O-4 | §3.4+§3.5 | AC-SPEC-1/2, AC-HASH-1 | debt-closure | CODE-MODULE-SPEC | 0f0e82e |

## v1.12.0 delta（embedding API 重构）

| Spec | Feature | PRD 模块 | AC | PMS | CMS ref | Commit |
|---|---|---|---|---|---|---|
| SPEC-F-Q-1 | F-Q-1 | §3.1 | AC-EA-1/2 | embedding-api | CODE-MODULE-SPEC | 53cd582 |
| SPEC-F-Q-2 | F-Q-2 | §3.2 | AC-DIM-1/2 | embedding-api | CODE-MODULE-SPEC | 53cd582 |
| SPEC-F-Q-3 | F-Q-3 | §3.3 | AC-FB-1/2 | embedding-api | CODE-MODULE-SPEC | 53cd582 |
| SPEC-F-Q-4 | F-Q-4 | §3.4 | AC-TEST-1/2/3 | embedding-api | CODE-MODULE-SPEC | 53cd582 |

### v1.12.0 — embedding API pivot

| Commit | Task | Spec | Feature | PRD Item | AC | Test |
|---|---|---|---|---|---|---|
| f4f4869 | T-F-Q-1 | SPEC-F-Q-1 | F-Q-1 | PRD-EA-1 | AC-EA-1, AC-EA-2 | test_embedding_index (4), test_embedding_degradation (4) |
| f4e9f04 | T-F-Q-2 | SPEC-F-Q-2 | F-Q-2 | PRD-EA-2 | AC-DIM-1, AC-DIM-2 | test_embedding_index::test_dim_change, test_emb_ac1 |
| 4818926 | T-F-Q-3 | SPEC-F-Q-3 | F-Q-3 | PRD-EA-3 | AC-FB-1, AC-FB-2 | test_semantic_search::test_sem_fb1, test_sem_fb2 |
| 65f036f | T-F-Q-4 | SPEC-F-Q-4 | F-Q-4 | PRD-EA-4 | AC-TEST-1/2/3 | test_embedding_* (mock), test_ci_workflow, test_embedding_benchmark |

### v1.13.0 — E2E 收尾轮（backward: Test → Commit → Task → Spec → Feature → PRD AC）

| Test | Commit | Task | Spec | Feature | PRD AC |
|---|---|---|---|---|---|
| test_ingest_directory.py (5 tests) | 0669d98 | T-F-R-1 | SPEC-F-R-1 | F-R-1 | AC-A-1..5 |
| test_embedding_benchmark.py (4 new tests) | dc6d299 | T-F-R-2 | SPEC-F-R-2 | F-R-2 | AC-B-1..4 |
| test_workflow_rest_db.py alias tests (2) | 3284262 | T-F-R-3 | SPEC-F-R-3 | F-R-3 | AC-C-1 |
| test_changelog.py (2 tests) | 3284262 | T-F-R-3 | SPEC-F-R-3 | F-R-3 | AC-C-2..3 |
| test_coverage_config.py (1 test) | 8d9ccca | T-F-R-4 | SPEC-F-R-4 | F-R-4 | AC-D-1 |
| CI pytest --cov (67%) | 8d9ccca+218c398 | T-F-R-4 | SPEC-F-R-4 | F-R-4 | AC-D-2 |
| test_retrospective_closure.py (2 tests) | 895c8bf | T-F-R-5 | SPEC-F-R-5 | F-R-5 | AC-E-1..2 |
| test_linter_coverage.py (25) | 8d9ccca | T-F-R-4 | SPEC-F-R-4 | F-R-4 | AC-D-2 (coverage) |
| test_code_wiki_coverage.py (15) | 8d9ccca | T-F-R-4 | SPEC-F-R-4 | F-R-4 | AC-D-2 (coverage) |
| test_concept_graph_coverage.py (22) | 8d9ccca | T-F-R-4 | SPEC-F-R-4 | F-R-4 | AC-D-2 (coverage) |
| test_archiver_coverage.py (12) | 218c398 | T-F-R-4 | SPEC-F-R-4 | F-R-4 | AC-D-2 (coverage) |
| test_feedback_coverage.py (16) | 218c398 | T-F-R-4 | SPEC-F-R-4 | F-R-4 | AC-D-2 (coverage) |

## v1.14.0 delta（semantic 性能优化，backward: Test → Commit → Task → Spec → Feature → PRD AC）

| Test | Commit | Task | Spec | Feature | PRD AC |
|---|---|---|---|---|---|
| test_semantic_cache_config.py (5 tests) | 22d25e6 | T-F-S-1 | SPEC-F-S-1 | F-S-1 | AC-A-1..5 |
| test_ann_search.py (5 tests) | 9e456df | T-F-S-2 | SPEC-F-S-2 | F-S-2 | AC-B-1..5 |
| test_related_pages_ann.py (2 tests) | 9e456df | T-F-S-2 | SPEC-F-S-2 | F-S-2 | AC-B-5 |
| test_embedding_benchmark.py (+1 new, AC-C-2/3 benchmark_e2e) | 99bc06c | T-F-S-3 | SPEC-F-S-3 | F-S-3 | AC-C-1..5 |

## v1.15.0 delta（agent/link 能力，backward: Test → Commit → Task → Spec → Feature → PRD AC）

| Test | Commit | Task | Spec | Feature | PRD AC |
|---|---|---|---|---|---|
| test_custom_agents.py (7 tests) | 53cd582 | T-F-T-1 | SPEC-F-T-1 | F-T-1 | AC-A-1, AC-A-2, AC-A-3 |
| test_agents_api.py (9 tests) | 53cd582+59f9552 | T-F-T-1/T-F-T-3 | SPEC-F-T-1/SPEC-F-T-3 | F-T-1, F-T-3 | AC-A-4, AC-C-3, AC-C-4 |
| test_links_apply.py (4 tests) | 8f6ad2b | T-F-T-2 | SPEC-F-T-2 | F-T-2 | AC-B-1..4 |
| test_agent_activity.py (8 tests) | 59f9552 | T-F-T-3 | SPEC-F-T-3 | F-T-3 | AC-C-1, AC-C-2 |

## v1.16.0 delta（realtime 仪表盘 v4.3，backward: Test → Commit → Task → Spec → Feature → PRD AC）

| Test | Commit | Task | Spec | Feature | PRD AC |
|---|---|---|---|---|---|
| test_agent_roster_render.test.tsx | c42df02 | T-F-U-1 | SPEC-F-U-1 | F-U-1 | AC-D-1 |
| test_agent_activity_detail.test.tsx | c42df02 | T-F-U-1 | SPEC-F-U-1 | F-U-1 | AC-D-2 |
| test_agent_activity_null.test.tsx | c42df02 | T-F-U-1 | SPEC-F-U-1 | F-U-1 | AC-D-3 |
| test_agent_activity_404.test.tsx | c42df02 | T-F-U-1 | SPEC-F-U-1 | F-U-1 | AC-D-4 |
| test_workflow_list_render.test.tsx | a95e476 | T-F-U-2 | SPEC-F-U-2 | F-U-2 | AC-D-5 |
| test_workflow_running_top.test.tsx | a95e476 | T-F-U-2 | SPEC-F-U-2 | F-U-2 | AC-D-6 |
| test_workflow_ws_update.test.tsx | a95e476 | T-F-U-2 | SPEC-F-U-2 | F-U-2 | AC-D-7 |
| test_ws_disconnect_polling_degraded.test.tsx | 0704e5a | T-F-U-3 | SPEC-F-U-3 | F-U-3 | AC-D-8 |

## v1.17.0 delta（desktop 完成 v4.4，backward: Test → Commit → Task → Spec → Feature → PRD AC）

| Test | Commit | Task | Spec | Feature | PRD AC |
|---|---|---|---|---|---|
| test_version_consistency.py | f922a99 | T-F-V-1 | SPEC-F-V-1 | F-V-1 | AC-V-1 |
| test_tauri_config_consistency.py | f922a99 | T-F-V-1 | SPEC-F-V-1 | F-V-1 | AC-V-2 |
| test_web_dist_integration.py | 19578ef | T-F-V-2 | SPEC-F-V-2 | F-V-2 | AC-W-1 |
| test_web_dev_integration.py | 19578ef | T-F-V-2 | SPEC-F-V-2 | F-V-2 | AC-W-2 |
| test_tauri_build_smoke.py (skipif no cargo) | 6bb6949 | T-F-V-3 | SPEC-F-V-3 | F-V-3 | AC-B-1 |
| test_bundle_targets_config.py | 6bb6949 | T-F-V-3 | SPEC-F-V-3 | F-V-3 | AC-B-2 |
| test_port_convergence.py | 1ca63a1 | T-F-V-4 | SPEC-F-V-4 | F-V-4 | AC-C-1 |
| test_prod_backend_connection.py | 1ca63a1 | T-F-V-4 | SPEC-F-V-4 | F-V-4 | AC-C-2 |
| test_cors_expansion.py | 1ca63a1 | T-F-V-4 | SPEC-F-V-4 | F-V-4 | AC-C-3 |

## v1.18.0 delta（per-request workspace 注入 + O4 tag 流程修复，backward: Test → Commit → Task → Spec → Feature → PRD AC）

| Test | Commit | Task | Spec | Feature | PRD AC |
|---|---|---|---|---|---|
| test_workspace_contextvar.py | [TBD] | T-F-W-1 | SPEC-F-W-1 | F-W-1 | AC-WS-1, AC-WS-2 |
| test_workspace_isolation.py | [TBD] | T-F-W-1 | SPEC-F-W-1 | F-W-1 | AC-WS-3 |
| test_workspace_cli_compat.py | [TBD] | T-F-W-1 | SPEC-F-W-1 | F-W-1 | AC-WS-4 |
| test_workspace_signature.py | [TBD] | T-F-W-1 | SPEC-F-W-1 | F-W-1 | AC-WS-5 |
| test_workspace_validation.py | [TBD] | T-F-W-1 | SPEC-F-W-1 | F-W-1 | AC-WS-1（补充） |
| test_workspace_thread_propagation.py | [TBD] | T-F-W-1 | SPEC-F-W-1 | F-W-1 | AC-WS-1（补充） |
| test_o4_tag_flow.py | [TBD] | T-F-W-2 | SPEC-F-W-2 | F-W-2 | AC-O4-1, AC-O4-2 |
| test_release_flow_docs.py | [TBD] | T-F-W-2 | SPEC-F-W-2 | F-W-2 | AC-O4-1（文档） |
