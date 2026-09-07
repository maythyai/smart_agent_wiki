# Test Index — TMS 索引

> 全部模块测试说明书。每条 PRD AC ≥1 用例；未映射 AC 在 COVERAGE-REPORT 显式标缺口。

| module | slug | 用例数 | AC 覆盖 | 状态 | file |
|---|---|---|---|---|---|
| e2e-usability | e2e-usability | 11 | AC-E2E-1/2, AC-TEST-2(部分) | ready | TMS-e2e-usability.md |
| claim-alignment | claim-alignment | 6 | AC-ALIGN-1/2 | ready | TMS-claim-alignment.md |
| security-hardening | security-hardening | 10 | AC-SEC-1/2/3 | ready | TMS-security-hardening.md |
| observability | observability | 6 | AC-OBS-1/2 | ready | TMS-observability.md |
| test-gate | test-gate | 6 | AC-TEST-1/2 | ready | TMS-test-gate.md |

## 汇总
- 用例总数：39
- PRD AC 覆盖：11/11（AC-E2E-1/2, AC-ALIGN-1/2, AC-SEC-1/2/3, AC-OBS-1/2, AC-TEST-1/2）
- 状态：全 ready（边界已定）；[TBD] 项见各 TMS 缺口

## TMS 红线
- 继承 PMS 边界，不发明 PMS 未声明模块。
- 变更只产 delta 增量用例，不推倒重来。

## 05 增量（2026-09-01，feat/hardening-wave1-slice）
- 新增 30 用例：e2e-usability +5（F-A-1）、claim-alignment +4（F-B-1）、security-hardening +21（F-C-3 ×6, F-C-4 ×15）。
- 用例总数：39 → 69。
- 新覆盖 AC：AC-SEC-1（URL guard track）/ AC-SEC-3（限流 429）/ AC-ALIGN-1（宣称 diff）/ AC-E2E-1（冒烟骨架 partial）。
- ruff 未跑（未装，[TBD]）；coverage 基线 deferred（T-F-E-1-1）。

## v1.10.0 delta（embedding 语义搜索）
- 模块：embedding（PMS-embedding），ADR-010 向量存储 + 检索融合。
- 新增 12 AC（AC-EMB-1/2/3, AC-SEM-1/2/3, AC-LINK-1/2/3, AC-TEST-1/2/3），全映射。
- 测试文件：test_embedding_index.py（importorskip）、test_semantic_search.py（importorskip）、test_related_pages_embedding.py（importorskip）、test_embedding_degradation.py（mock 降级）、test_ci_workflow.py（扩）。
- 用例总数：69 → 69 + 12 = 81（[TBD-impl] 实施后落定）。
- 新覆盖 AC：AC-EMB-1/2/3, AC-SEM-1/2/3, AC-LINK-1/2/3, AC-TEST-1/2/3（12 条全映射）。
- TMS delta 见 `TMS-DELTA-v1.10.0.md`。

## v1.11.0 delta（债务收口 IV / bug fix）
- 模块：debt-closure（PMS-debt-closure），ADR-011 semantic search cache 策略。
- 新增 12 AC（AC-CACHE-1/2/3/4, AC-COV-1/2, AC-WF-1/2/3, AC-SPEC-1/2, AC-HASH-1），全映射。
- 测试文件：test_semantic_cache.py（mock，无 SDK）、tests/unit/engines/compile/（新建 7 文件 + conftest，20 用例）、test_workflow_rest_db.py（in-memory DB）、test_spec_naming.py（grep + subprocess）、test_hash_consistency.py（git rev-list）。
- 用例总数：81 → 81 + 12 = 93（[TBD-impl] 实施后落定）。
- 新覆盖 AC：AC-CACHE-1/2/3/4, AC-COV-1/2, AC-WF-1/2/3, AC-SPEC-1/2, AC-HASH-1（12 条全映射）。
- TMS delta 见 `TMS-DELTA-v1.11.0.md`。

## v1.12.0 delta（embedding API 重构）
- 模块：embedding-api（PMS-embedding-api），ADR-012 embedding provider 选型 litellm API + 本地 ST fallback。
- 新增 9 AC（AC-EA-1/2, AC-DIM-1/2, AC-FB-1/2, AC-TEST-1/2/3），全映射。
- 测试文件：test_embedding_index.py（改 API mock，去 importorskip）、test_semantic_search.py（改 API mock，去 importorskip）、test_related_pages_embedding.py（改 API mock，去 importorskip）、test_embedding_degradation.py（扩 API 不可用场景）、test_ci_workflow.py（扩 importorskip 检测更新）、test_embedding_benchmark.py（新建 benchmark）。
- 用例总数：93 → 93 + 9 = 102（[TBD-impl] 实施后落定）。
- 新覆盖 AC：AC-EA-1/2, AC-DIM-1/2, AC-FB-1/2, AC-TEST-1/2/3（9 条全映射）。
- TMS delta 见 `TMS-DELTA-v1.12.0.md`。

## v1.13.0 delta（E2E 收尾轮）
- 模块：e2e-tail（PMS-e2e-tail），ADR-013 ingest 递归 + benchmark 方法论。
- 新增 16 AC（AC-A-1..5, AC-B-1..4, AC-C-1..3, AC-D-1..2, AC-E-1..2），全映射。
- 测试文件：test_ingest_directory.py（新建 5）、test_embedding_benchmark.py（扩 4，marker）、test_workflow_rest_db.py（扩 2）、test_changelog.py（新建 2）、test_coverage_config.py（改 1）、test_coverage_gate.py（改 1）、test_retrospective_closure.py（新建 2）+ 5 覆盖率测试文件（90 用例）。
- 用例总数：102 → 102 + 16 + 90 = 208（05 实施后落定 2179 passed）。
- 新覆盖 AC：AC-A-1..5, AC-B-1..4, AC-C-1..3, AC-D-1..2, AC-E-1..2（16 条全映射）。
- TMS delta 见 `TMS-DELTA-v1.13.0.md`。

## v1.14.0 delta（semantic 性能优化）
- 模块：semantic-perf（PMS-semantic-perf），ADR-014 ANN 向量索引选型 hnswlib + numpy 批量 cosine 改进。
- 新增 15 AC（AC-A-1..5, AC-B-1..5, AC-C-1..5），全映射。
- 测试文件：test_semantic_cache_config.py（新建 5）、test_ann_search.py（新建 5）、test_related_pages_ann.py（新建 1）、test_embedding_benchmark.py（扩 5）。
- 用例总数：[TBD-impl] 实施后落定（基线 2179 passed）。
- 新覆盖 AC：AC-A-1..5, AC-B-1..5, AC-C-1..5（15 条全映射）。
- TMS delta 见 `TMS-DELTA-v1.14.0.md`。

## v1.15.0 delta（agent/link 能力）
- 模块：agent-link（PMS-agent-link），ADR-015 agent 角色注册表 + 活动聚合机制。
- 新增 12 AC（AC-A-1..4, AC-B-1..4, AC-C-1..4），全映射。
- 测试文件：test_custom_agents.py（新建 3）、test_agents_rest.py（新建/扩 3）、test_links_apply.py（新建 4）、test_agent_activity.py（新建 2）。
- 用例总数：[TBD-impl] 实施后落定（基线 2192 passed）。
- 新覆盖 AC：AC-A-1..4, AC-B-1..4, AC-C-1..4（12 条全映射）。
- TMS delta 见 `TMS-DELTA-v1.15.0.md`。

## v1.16.0 delta（realtime 仪表盘 v4.3）
- 模块：dashboard（PMS-dashboard），ADR-016 realtime 仪表盘更新策略 polling + WS 双源。
- 新增 8 AC（AC-D-1..8），全映射。AC-D-9（后端不回归）为系统级 NFR。
- 测试文件：test_agent_roster_render.test.tsx（新建 1）、test_agent_activity_detail.test.tsx（新建 1）、test_agent_activity_null.test.tsx（新建 1）、test_agent_activity_404.test.tsx（新建 1）、test_workflow_list_render.test.tsx（新建 1）、test_workflow_running_top.test.tsx（新建 1）、test_workflow_ws_update.test.tsx（新建 1）、test_ws_disconnect_polling_degraded.test.tsx（新建 1）。
- 用例总数：[TBD-impl] 实施后落定（基线 2220 passed，前端 vitest 新增 8 用例）。
- 新覆盖 AC：AC-D-1..8（8 条全映射，vitest + @testing-library/react mock）。
- TMS delta 见 `TMS-DELTA-v1.16.0.md`。

## v1.17.0 delta（desktop 完成 v4.4）
- 模块：desktop（PMS-desktop），ADR-017 desktop 嵌入策略 + 端口收敛。
- 新增 9 AC（AC-V-1/2, AC-W-1/2, AC-B-1/2, AC-C-1/2/3），全映射。
- 测试文件：test_version_consistency.py（新建，版本一致性校验）、test_tauri_config_consistency.py（新建，tauri.conf.json 配置审查）、test_web_dist_integration.py（新建，web/dist 集成验证）、test_web_dev_integration.py（新建，dev 模式验证）、test_tauri_build_smoke.py（新建，tauri build 冒烟，skipif no cargo）、test_bundle_targets_config.py（新建，bundle.targets 配置）、test_port_convergence.py（新建，端口收敛 8080→8000）、test_prod_backend_connection.py（新建，prod 连接配置）、test_cors_expansion.py（新建，CORS localhost:5173）。
- 用例总数：[TBD-impl] 实施后落定（基线 2217 passed + 8 配置测试 + 1 skipif smoke）。
- 新覆盖 AC：AC-V-1/2, AC-W-1/2, AC-B-1/2, AC-C-1/2/3（9 条全映射，pytest + json/re 文件检查）。
- TMS delta 见 `TMS-DELTA-v1.17.0.md`。
