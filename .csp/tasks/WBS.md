# WBS — 任务分解（20 Task，1:1 对应 Spec）

> Task 源于 Spec 维度，1 Task/Spec（S/M hardening 粒度合适，避免碎片化）。每 Task ≤4h。deps 镜像 decomposition Feature 依赖。

| task_id | spec_ref | 描述 | 类型 | 估时 | depends_on | files | acceptance | pms_module |
|---|---|---|---|---|---|---|---|---|
| T-F-A-1-1 | SPEC-F-A-1 | 冒烟命令骨架+fresh 库初始化+节点报告 | backend-cli | S | — | src/saw/drivers/cli/commands/smoke_cmd.py [TBD], main.py | AC-E2E-1 | e2e-usability |
| T-F-A-2-1 | SPEC-F-A-2 | ingest(md+url)+compile 增量冒烟节点+溯源断言 | test | M | T-F-A-1-1 | commands/smoke_cmd.py, fixtures/ | AC-E2E-1 | e2e-usability |
| T-F-A-3-1 | SPEC-F-A-3 | query(关键词+NL)冒烟+citation 断言 | test | M | T-F-A-1-1 | commands/smoke_cmd.py | AC-E2E-1 | e2e-usability |
| T-F-A-4-1 | SPEC-F-A-4 | govern(lint+verify)+learn(distill)冒烟 | test | M | T-F-A-1-1 | commands/smoke_cmd.py | AC-E2E-1 | e2e-usability |
| T-F-A-5-1 | SPEC-F-A-5 | 离线 fallback 冒烟+降级标记 | test | M | T-F-A-2-1,T-F-A-3-1,T-F-A-4-1 | commands/smoke_cmd.py | AC-E2E-2 | e2e-usability |
| T-F-A-6-1 | SPEC-F-A-6 | ci.yml smoke job+退出码门禁 | infra-ci | S | T-F-A-5-1 | .github/workflows/ci.yml | AC-E2E-1,AC-TEST-2 | e2e-usability |
| T-F-B-1-1 | SPEC-F-B-1 | claim_diff.sh(grep 宣称 vs entry-points) | infra-script | M | — | scripts/claim_diff.sh | AC-ALIGN-1 | claim-alignment |
| T-F-B-2-1 | SPEC-F-B-2 | gen_capabilities.sh→docs/CAPABILITIES.md(file:line) | infra-script | M | T-F-B-1-1 | scripts/gen_capabilities.sh, docs/CAPABILITIES.md | AC-ALIGN-2 | claim-alignment |
| T-F-B-3-1 | SPEC-F-B-3 | README/docs 修正+deep_audit 历史标注 | doc | S | T-F-B-1-1 | README*.md, docs/*audit*.md, reconcile-log.md | AC-ALIGN-2 | claim-alignment |
| T-F-C-1-1 | SPEC-F-C-1 | 裸路由检测+权限矩阵文档(auth_dep 校验) | test-security | M | — | scripts/security_check.sh [TBD], .csp/artifacts/ | AC-SEC-1 | security-hardening |
| T-F-C-2-1 | SPEC-F-C-2 | receipt 全链路闭环+链式校验(agent+write_queue) | backend-security | M | — | write_queue/dispatcher.py, adapters/crypto/ed25519.py | AC-SEC-2 | security-hardening |
| T-F-C-3-1 | SPEC-F-C-3 | 限流双轨验证(429+Retry-After) | test-security | S | — | api/rate_limit.py | AC-SEC-3 | security-hardening |
| T-F-C-4-1 | SPEC-F-C-4 | URL 守卫全覆盖审计 | test-security | S | — | adapters/url_guard.py | AC-SEC-1(辅) | security-hardening |
| T-F-C-5-1 | SPEC-F-C-5 | 前后端 token 同源核验+补齐 [TBD] | backend-security | M | — | drivers/web/routes/auth.py, web/ | (token) | security-hardening |
| T-F-D-1-1 | SPEC-F-D-1 | logger 收敛至 init_observability+lint | backend | M | — | middleware/observability.py, 各模块 | AC-OBS-1 | observability |
| T-F-D-2-1 | SPEC-F-D-2 | trace_id contextvar 贯穿 engines→sinks | backend | M | T-F-D-1-1 | middleware/observability.py, engines/, write_queue/ | AC-OBS-1 | observability |
| T-F-D-3-1 | SPEC-F-D-3 | /health/ready 真实化+JSON 日志默认 | backend | S | — | drivers/web/health.py, observability.py | AC-OBS-2 | observability |
| T-F-E-1-1 | SPEC-F-E-1 | coverage 基线实测+阈值设定 [TBD] | infra-ci | M | — | .github/workflows/ci.yml, .csp/artifacts/coverage-baseline.md | (基线) | test-gate |
| T-F-E-2-1 | SPEC-F-E-2 | 核心引擎 coverage 门禁(≥80% 阻断) | infra-ci | M | T-F-E-1-1 | ci.yml | AC-TEST-1 | test-gate |
| T-F-E-3-1 | SPEC-F-E-3 | CI 集成(单测+冒烟+coverage+报告) | infra-ci | M | T-F-A-6-1,T-F-E-2-1 | ci.yml | AC-TEST-2 | test-gate |
| T-F-Z-1-1 | —（无 spec） | ruff baseline 收口([tool.ruff]+全库 UP017/BLE001/S110 修) | tech-debt | S | — | pyproject.toml, src/saw/** | AC-LINT-1 | test-gate |
| T-F-Z-2-1 | —（无 spec） | roadmap narrative 重写(v1.1/1.2 对齐+v1.3/1.4 重定义) | tech-debt | S | — | docs/strategy/ROADMAP.md | AC-DOC-1 | e2e-usability |
| T-F-Z-3-1 | —（无 spec） | v1.2.0 行为变更迁移文档(JSON日志/health 503) | tech-debt | S | — | docs/QUICKSTART.md, docs/MIGRATION.md | AC-DOC-2 | observability |
| T-F-P-1-1 | —（无 spec） | RBAC深化(Cedar热加载+权限矩阵e2e) | platform-team | M | — | src/saw/auth/cedar_policy.py, .csp/artifacts/security-matrix.md | AC-SEC-4, AC-SEC-5 | security-hardening |
| T-F-P-2-1 | —（无 spec） | 团队部署(docker-compose.prod+healthcheck+secrets env) | platform-team | S | — | docker/docker-compose.prod.yml | AC-DEPLOY-1, AC-DEPLOY-2 | security-hardening |
| T-F-P-3-1 | —（无 spec） | 可观测闭环(saw health 巡检+saw audit receipts) | platform-team | M | — | src/saw/drivers/cli/commands/health_cmd.py, audit_cmd.py | AC-OBS-3, AC-OBS-4 | observability |
| T-F-P-4-1 | —（无 spec，ADR-005） | 多workspace隔离(schema前缀+migration v8+授权绑定) | platform-team | M | T-F-P-1-1 | src/saw/db/migrations.py, auth/permissions.py | AC-WS-1, AC-WS-2 | security-hardening |
| T-F-Z-4-1 | —（无 spec） | ruff F401/F841 收口(import审计+27死赋值修+移除ignore) | tech-debt | M | — | pyproject.toml, src/saw/** | AC-LINT-2 | test-gate |
| T-F-Z-5-1 | —（无 spec） | heavy-SDK learn 3测试 importorskip+ci移除ignore | tech-debt | S | — | tests/unit/engines/learn/, .github/workflows/ci.yml | AC-LINT-3 | test-gate |
| T-F-I-1 | SPEC-F-I-1 | workflow CLI(run/validate/resume/status/lint)+resume()续跑 | backend-cli | M | T-F-I-4 | commands/workflow_cmd.py, engines/collaborate/workflow_executor.py, main.py | AC-WF-1, AC-WF-2 | intelligence-adaptation |
| T-F-I-2 | SPEC-F-I-2 | Learn CLI(distill 在线+gaps) | backend-cli | S | — | commands/learn_cmd.py, main.py | AC-LR-1, AC-LR-2 | intelligence-adaptation |
| T-F-I-3 | SPEC-F-I-3 | Token bench CLI(实测节省%) | backend-cli | S | — | commands/token_cmd.py, main.py | AC-TK-1 | intelligence-adaptation |
| T-F-I-4 | SPEC-F-I-4 | agent 角色一致性 lint(saw workflow lint) | backend-cli | S | — | commands/workflow_cmd.py | AC-AG-1 | intelligence-adaptation |
| T-F-Z-6 | SPEC-F-Z-6 | ruff F841 27 死赋值手修+移除 ignore 启用 | tech-debt | M | T-F-I-1,T-F-Z-7 | pyproject.toml, src/saw/** | AC-LINT-2(续) | test-gate |
| T-F-Z-7 | SPEC-F-Z-7 | workspace 全查询路径路由(repo 层注入 scope) | backend | L | — | engines/query/engine.py, engines/ingest/pipeline.py, adapters/storage/*, domain/protocols.py | AC-WS-3 | intelligence-adaptation |
| T-F-Z-8 | SPEC-F-Z-8 | Cedar policy reload CLI(saw policy reload) | backend-cli | S | — | commands/policy_cmd.py, main.py | AC-SEC-5(续) | security-hardening |
| T-F-Z-9 | SPEC-F-Z-9 | query 子模块测试+fail_under 60→65 | test | M | — | tests/unit/engines/query/*, pyproject.toml | AC-COV-1 | test-gate |
| T-F-J-1 | SPEC-F-J-1 | tree_mode+compiler 注入 workspace scope（QueryEngine 透传） | backend | M | — | engines/query/tree_mode.py, engines/query/compiler.py, engines/query/engine.py, drivers/web/app.py, drivers/cli/commands/query_cmd.py | AC-WS-4 | debt-closure |
| T-F-J-2 | SPEC-F-J-2 | insert 持久化 workspace_id + ingest 透传 | backend | M | — | adapters/storage/claims_repository.py, engines/ingest/pipeline.py | AC-WS-5 | debt-closure |
| T-F-J-3 | SPEC-F-J-3 | query 深覆盖（engine/compare/tree_mode）+ fail_under 63→65 | test | M | T-F-J-1 | tests/unit/engines/query/*, pyproject.toml | AC-COV-2 | test-gate |
| T-F-J-4 | SPEC-F-J-4 | policy reload Web admin 端点（admin-only） | backend | S | — | drivers/web/routes/admin.py, drivers/web/app.py | AC-SEC-6 | security-hardening |
| T-F-K-1 | SPEC-F-K-1 | graph workspace 隔离（migration v9 + entity domain + GraphSink 写 + graph_traverse 读 + QueryEngine 透传） | backend | M | — | db/migrations.py, domain/*.py, write_queue/sinks/graph_sink.py, engines/query/graph_traverse.py, engines/query/engine.py, engines/ingest/pipeline.py, drivers/web/app.py, drivers/cli/commands/query_cmd.py | AC-WS-6 | graph-workspace |
| T-F-K-2 | SPEC-F-K-2 | scope 传播清理（tree_mode/compiler 显式 workspace_id，去 setattr） | backend | S | T-F-K-1 | engines/query/tree_mode.py, engines/query/compiler.py, engines/query/engine.py | AC-ARCH-1 | graph-workspace |
| T-F-K-3 | SPEC-F-K-3 | synthesize 覆盖（engine+scheduler）+ fail_under 63→64 | test | M | T-F-K-1 | tests/unit/engines/synthesize/*, pyproject.toml | AC-COV-3 | test-gate |
| T-F-L-1 | SPEC-F-L-1 | 智能链接建议 + 链接审计 bundle（saw links suggest/audit） | backend-cli | M | — | commands/links_cmd.py, main.py | AC-LINK-1, AC-LINK-2 | smart-linking |
| T-F-L-3 | SPEC-F-L-3 | AI 摘要（saw summarize） | backend-cli | S | — | commands/summarize_cmd.py, main.py | AC-SUM-1 | smart-linking |
| T-F-M-1 | SPEC-F-M-1 | saw workflow list（durable 历史，workflow_executions v4） | backend-cli | S | — | commands/workflow_cmd.py, main.py | AC-WF-3 | agent-viz |
| T-F-M-2 | SPEC-F-M-2 | saw agents（6-role roster CLI） | backend-cli | S | — | commands/agents_cmd.py, main.py | AC-AG-2 | agent-viz |
| T-F-M-3 | SPEC-F-M-3 | GET /api/v1/agents（roster REST） | backend | S | — | api/routes/collaborate.py | AC-API-1 | agent-viz |
| T-F-N-1 | SPEC-F-N-1 | embedding_store migration v10 + EmbeddingSink + Write Queue 注册 + `saw search rebuild-embeddings` 重建命令 | db-migration | M | — | db/migrations.py, write_queue/sinks/embedding_sink.py, engines/ingest/pipeline.py, drivers/cli/commands/search_cmd.py, drivers/cli/main.py | AC-EMB-1, AC-EMB-2, AC-EMB-3 | embedding |
| T-F-N-2 | SPEC-F-N-2 | QueryEngine `_semantic_search()` + `saw search --mode semantic` CLI + REST `mode=semantic` + 降级 BM25 | backend-api | M | T-F-N-1 | engines/query/engine.py, drivers/cli/commands/search_cmd.py, drivers/web/routes/search.py, api/routes/query_ingest_learn.py | AC-SEM-1, AC-SEM-2, AC-SEM-3 | embedding |
| T-F-N-3 | SPEC-F-N-3 | `compute_related_pages()` 增 embedding 第 4 信号（权重 2.5）+ RelatedPage `embedding_sim` + links_cmd 透传 conn | backend-logic | M | T-F-N-1 | engines/query/related_pages.py, drivers/cli/commands/links_cmd.py | AC-LINK-1, AC-LINK-2, AC-LINK-3 | embedding |
| T-F-N-4 | SPEC-F-N-4 | importorskip 测试策略（3 文件 importorskip + 降级测试分离 mock）+ ci_workflow 扩 importorskip 断言 | test | S | T-F-N-1 | tests/unit/test_embedding_index.py, tests/unit/test_semantic_search.py, tests/unit/test_related_pages_embedding.py, tests/unit/test_embedding_degradation.py, tests/unit/test_ci_workflow.py | AC-TEST-1, AC-TEST-2, AC-TEST-3 | embedding |
| T-F-O-1 | SPEC-F-O-1 | `_semantic_search` 入口插 cache.get + 出口插 cache.set（复用 get_cache() 单例 + mode=semantic key 隔离 + TTL 300s + rebuild-embeddings 补 cache.clear() 钩子 + fallback/index_empty 不缓存） | backend-logic | M | — | engines/query/engine.py, engines/query/cache.py, drivers/cli/commands/search_cmd.py | AC-CACHE-1, AC-CACHE-2, AC-CACHE-3, AC-CACHE-4 | debt-closure |
| T-F-O-2 | SPEC-F-O-2 | compile/compiler.py 深覆盖（新建 tests/unit/engines/compile/ 7 测试文件 + conftest 20 用例覆盖 30 函数）+ pyproject.toml fail_under 64→65 | test | L | — | tests/unit/engines/compile/*, pyproject.toml | AC-COV-1, AC-COV-2 | debt-closure |
| T-F-O-3 | SPEC-F-O-3 | collaborate.py list_workflows 改读 workflow_executions DB 表 + merge live in-memory running + conn=None fallback + 无表 auto-migrate | backend-api | M | — | api/routes/collaborate.py, drivers/cli/commands/workflow_cmd.py | AC-WF-1, AC-WF-2, AC-WF-3 | debt-closure |
| T-F-O-4 | SPEC-F-O-4 | SPEC-F-N-1.md L27/L133/L189 命名回更（saw search rebuild-embeddings→saw rebuild-embeddings）+ ROADMAP/lifecycle-state tag hash @3865c75 三处复核 | docs | S | — | .csp/specs/SPEC-F-N-1.md, docs/strategy/ROADMAP.md, .csp/lifecycle-state.json | AC-SPEC-1, AC-SPEC-2, AC-HASH-1 | debt-closure |
| T-F-Q-1 | SPEC-F-Q-1 | `embed_texts()` 改调 `litellm.embedding` + 新增 `EmbeddingSettings`（复用 `LLMSettings` 范式）+ `_api_embedding_available`/`_embed_via_api`/`_normalize` + `embeddings_available` 改 API OR ST + `detect_tier._embeddings_available` 改 API OR ST；签名不变 | backend-logic | M | — | src/saw/adapters/embeddings.py, src/saw/config/settings.py | AC-EA-1, AC-EA-2 | embedding-api |
| T-F-Q-2 | SPEC-F-Q-2 | `EmbeddingSink.write`/`_upsert_embedding` model 列动态化 + `rebuild_embeddings` 维度检测适配（provider 换了自动走 API/ST）；表结构不变（v10 已有 dim+model） | backend-logic | M | T-F-Q-1 | src/saw/write_queue/sinks/embedding_sink.py, src/saw/drivers/cli/commands/search_cmd.py | AC-DIM-1, AC-DIM-2 | embedding-api |
| T-F-Q-3 | SPEC-F-Q-3 | 本地 ST 可选 fallback：`embed_texts` 三级路由 API→ST→None 补 ST 分支 + `embeddings_available`/`_embeddings_available` OR 逻辑对称；向后兼容 v1.10.0 | backend-logic | M | T-F-Q-1 | src/saw/adapters/embeddings.py, src/saw/config/settings.py | AC-FB-1, AC-FB-2 | embedding-api |
| T-F-Q-4 | SPEC-F-Q-4 | 测试改 API mock（去 importorskip，7 测试改 mock litellm.embedding）+ 降级 mock 扩 API 不可用（4 测试）+ `test_ci_workflow` 更新 + 新建 `test_embedding_benchmark`（semantic vs BM25 召回+P99） | test | M | T-F-Q-1 | tests/unit/test_embedding_index.py, tests/unit/test_semantic_search.py, tests/unit/test_related_pages_embedding.py, tests/unit/test_embedding_degradation.py, tests/unit/test_ci_workflow.py, tests/unit/test_embedding_benchmark.py | AC-TEST-1, AC-TEST-2, AC-TEST-3 | embedding-api |
| T-F-S-1 | SPEC-F-S-1 | `engine.py` cache.get/set 条件分支（`SAW_SEMANTIC_CACHE_ENABLED`/`SAW_SEMANTIC_CACHE_THRESHOLD_MS`）+ `settings.py` 新增配置项 + `benchmark_semantic.py` 阈值读 env + `CHANGELOG.md` 追加 v1.14.0 条目 + 新建 `test_semantic_cache_config.py`（5 用例） | backend-logic | M | — | src/saw/engines/query/engine.py, src/saw/config/settings.py, scripts/benchmark_semantic.py, CHANGELOG.md, tests/unit/test_semantic_cache_config.py | AC-A-1, AC-A-2, AC-A-3, AC-A-4, AC-A-5 | semantic-perf |
| T-F-S-2 | SPEC-F-S-2 | `engine.py` `_semantic_search` 规模驱动切 ANN（hnswlib + numpy cosine fallback）+ `embeddings.py` 新增 `batch_cosine_similarity()` + `related_pages.py` 复用 ANN 路径 + `pyproject.toml` 新增 hnswlib + 新建 `test_ann_search.py` + `test_related_pages_ann.py` | backend-logic | L | — | src/saw/engines/query/engine.py, src/saw/adapters/embeddings.py, src/saw/engines/query/related_pages.py, pyproject.toml, tests/unit/test_ann_search.py, tests/unit/test_related_pages_ann.py | AC-B-1, AC-B-2, AC-B-3, AC-B-4, AC-B-5 | semantic-perf |
| T-F-S-3 | SPEC-F-S-3 | `benchmark_semantic.py` 更新（cache.stats() 真实度量 + ANN vs cosine P99 + 规模延迟曲线 100/500/1000/5000）+ 扩 `test_embedding_benchmark.py`（AC-C-1/4/5 CI 跑 + AC-C-2/3 marker skip） | infra | M | T-F-S-2 | scripts/benchmark_semantic.py, tests/unit/test_embedding_benchmark.py | AC-C-1, AC-C-2, AC-C-3, AC-C-4, AC-C-5 | semantic-perf |

## 汇总
- Task：20（1:1 Spec）；类型：backend-cli×1 / test×4 / infra-ci×4 / infra-script×2 / doc×1 / test-security×3 / backend-security×2 / backend×3
- 估时：S×8 / M×12；人日 [TBD]（无团队速率）
- deps 与 decomposition DEPENDENCY-GRAPH 一致（A1→A2/3/4→A5→A6→E3；B1→B2/3；D1→D2；E1→E2→E3）

## 05 实施状态（Wave 1 全完成，2026-09-03）
| task_id | status | commit | note |
|---|---|---|---|
| T-F-A-1-1 | done | d92ece0 | saw smoke skeleton, 5 tests |
| T-F-B-1-1 | done | 622859c | claim_diff.sh, 4 tests |
| T-F-C-1-1 | done | a4d8c9d | bare route detection + permission matrix, 23 tests |
| T-F-C-2-1 | done | 0c0cf33 | Ed25519 receipt chain (v7 migration + ReceiptStore + dispatcher wiring), 11 tests |
| T-F-C-3-1 | done | cf5b86b | rate-limit 429+Retry-After, 6 tests |
| T-F-C-4-1 | done | fece73d | URL guard coverage, 15 tests |
| T-F-C-5-1 | done | 7ad1a1a | frontend-backend token same-source verification, 16 tests (no code change — already same-source) |
| T-F-D-1-1 | done | 3850d4f | logger convergence lint tests (no scattered basicConfig), 3 tests |
| T-F-D-3-1 | done | 3850d4f | JSON log production default + engine-aware /health/ready, 6 tests |
| T-F-E-1-1 | done | 62d95ce | coverage baseline 62% total / 64% core measured |
- **Wave 1: 10/10 done → M1（基础硬化就绪）达成。**
- 全量回归 1853 passed, 3 skipped, 0 失败（2026-09-03）。
- ruff：新代码 clean；既有 baseline 有跨代码库 UP017/BLE001 tech debt（未在 Wave 1 scope，单独建 task）。
- Wave 2（7 Task）、Wave 3（3 Task）留后续周期。

## v1.3.0 实施状态（Wave 2/3 + debt，2026-09-03）
| task_id | status | commit | note |
|---|---|---|---|
| T-F-A-2-1 | done | 328027d | smoke ingest+compile node (provenance anchor + wiki page) |
| T-F-A-3-1 | done | 328027d | smoke query keyword node (citation) |
| T-F-A-4-1 | done | 328027d | smoke govern+learn node (lint/verify/distiller) |
| T-F-A-5-1 | done | 7adc651 | offline fallback smoke node (auto→search degraded) |
| T-F-A-6-1 | done | (ci.yml) | CI smoke job (`saw smoke` gate) |
| T-F-B-2-1 | done | (capabilities) | gen_capabilities.sh + CAPABILITIES.md (2 verified/213 unverified) |
| T-F-B-3-1 | done | b75a449 | reconcile-log pointer + drift D1/D3 status |
| T-F-D-2-1 | done | (trace) | trace_id propagates to write path (2 tests) |
| T-F-E-2-1 | done | (coverage) | ratchet fail_under=60 in pyproject (2 tests) |
| T-F-E-3-1 | done | (ci.yml) | CI coverage gate step (ignore heavy-SDK) |
| T-F-Z-1-1 | done | b945655 | ruff config + 2 F823 bug fixes; src/+tests/ green |
| T-F-Z-2-1 | done | 1a0894c | roadmap narrative rewrite (subagent) |
| T-F-Z-3-1 | done | 2bea49a | v1.2.0 behavior-change migration docs (subagent) |
- **v1.3.0: Wave 2/3 + debt 全 13 Task done → M2+M3 达成。**
- 全量回归 1874 passed, 3 skipped, 0 失败（2026-09-03）。
- ruff：新代码 clean；既有 baseline 有跨代码库 UP017/BLE001 tech debt（未在 Wave 1 scope，单独建 task）。
- Wave 2（7 Task）、Wave 3（3 Task）留后续周期。

## v1.4.0 实施状态（platform-team + debt 续，2026-09-03）
| task_id | status | commit | note |
|---|---|---|---|
| T-F-P-1-1 | done | (rbac) | Cedar hot-reload + 9 role×perm matrix e2e (AC-SEC-4/5) |
| T-F-P-2-1 | done | (compose) | self-contained docker-compose.prod + healthcheck + secrets env (AC-DEPLOY-1/2) |
| T-F-P-3-1 | done | (health/audit) | saw health 巡检 + saw audit --session (AC-OBS-3/4) |
| T-F-P-4-1 | done | (workspace) | migration v8 workspace_id + user_workspace_auth + isolation (AC-WS-1/2, ADR-005) |
| T-F-Z-4-1 | done | 5f3f4db | ruff F401 closure: 313 auto-fix, F401 enforced (F841 27 defer Z-4b) |
| T-F-Z-5-1 | done | 9d93e7d | heavy-SDK learn tests importorskip + CI --ignore removed (AC-LINT-3) |
- **v1.4.0: platform + debt 全 6 Task done → M4+M5+M6 达成。**
- 全量回归 1898 passed, 3 skipped；saw smoke 6/6 PASS；ruff src/+tests/ 0 errors（F401 启用）。

## v1.10.0 任务拆解（embedding，2026-09-04）
- 4 Task（1:1 Spec）：T-F-N-1（db-migration）/ T-F-N-2（backend-api）/ T-F-N-3（backend-logic）/ T-F-N-4（test）
- 2 Wave：Wave 1 T-F-N-1（migration v10 串行先行）→ Wave 2 T-F-N-2/N-3/N-4（全并行）
- DAG N-1→{N-2,N-3,N-4} 无环，与 decomposition 一致
- 详见 `.csp/tasks/TASKS-DELTA-v1.10.0.md`

## v1.12.0 任务拆解（embedding API 重构，2026-09-05）
- 4 Task（1:1 Spec）：T-F-Q-1（backend-logic provider 重构）/ T-F-Q-2（backend-logic 维度可配+重建检测）/ T-F-Q-3（backend-logic ST fallback）/ T-F-Q-4（test mock+benchmark）
- 2 Wave：Wave 1 T-F-Q-1（provider 重构前置）→ Wave 2 T-F-Q-2/Q-3/Q-4（全并行）
- DAG Q-1→{Q-2,Q-3,Q-4} 无环，与 decomposition 一致
- 详见 `.csp/tasks/TASKS-DELTA-v1.12.0.md`

## v1.14.0 任务拆解（semantic 性能优化，2026-09-06）
- 3 Task（1:1 Spec）：T-F-S-1（backend-logic cache 阈值可配）/ T-F-S-2（backend-logic ANN 索引）/ T-F-S-3（infra benchmark 更新）
- 2 Wave：Wave 1 T-F-S-1 / T-F-S-2（并行，engine.py 不同 section）→ Wave 2 T-F-S-3（依赖 S-2）
- DAG S-2→S-3 单向边，S-1 独立，无环，与 decomposition 一致
- 详见 `.csp/tasks/TASKS-DELTA-v1.14.0.md`

## v1.15.0 任务拆解（agent/link 能力，2026-09-06）
- 3 Task（1:1 Spec）：T-F-T-1（backend-logic 自定义角色注册）/ T-F-T-2（backend-logic links auto-apply）/ T-F-T-3（backend-logic agent 活动聚合）
- 1 Wave：Wave 1 T-F-T-1 / T-F-T-2 / T-F-T-3（全并行，3 Feature 互相独立无边）
- DAG 无环（3 独立节点，无边），与 decomposition 一致
- 详见 `.csp/tasks/TASKS-DELTA-v1.15.0.md`

| task_id | spec_ref | 描述 | 类型 | 估时 | depends_on | files | acceptance | pms_module |
|---|---|---|---|---|---|---|---|---|
| T-F-T-1 | SPEC-F-T-1 | `agents/__init__.py` 新增 `load_custom_agents` + `build_agent_roster` additive 合并 + `collaborate.py` list_agents custom 标记 + `agents_cmd.py` CLI custom 标注 + `workflow_parser.py` validate 含自定义角色 + 新建 `test_custom_agents.py` + 扩 `test_agents_rest.py` | backend-logic | M | — | src/saw/engines/collaborate/agents/__init__.py, src/saw/api/routes/collaborate.py, src/saw/drivers/cli/commands/agents_cmd.py, src/saw/engines/collaborate/workflow_parser.py, tests/unit/test_custom_agents.py, tests/unit/test_agents_rest.py | AC-A-1, AC-A-2, AC-A-3, AC-A-4 | agent-link |
| T-F-T-2 | SPEC-F-T-2 | `links_cmd.py` 新增 `apply` 子命令（dry-run/confirm + ## Related 段落插入 + frontmatter related 同步 + 去重 + WikiRepository.write 复用）+ 新建 `test_links_apply.py` | backend-logic | M | — | src/saw/drivers/cli/commands/links_cmd.py, tests/unit/test_links_apply.py | AC-B-1, AC-B-2, AC-B-3, AC-B-4 | agent-link |
| T-F-T-3 | SPEC-F-T-3 | 新建 `activity_tracker.py`（AgentActivityTracker event_bus subscriber + 内存计数器）+ `collaborate.py` GET /agents/{name}/activity + activity_summary + `app.py` lifespan init + `agents_cmd.py` activity 子命令 + 新建 `test_agent_activity.py` + 扩 `test_agents_rest.py` | backend-logic | M | — | src/saw/engines/collaborate/activity_tracker.py, src/saw/api/routes/collaborate.py, src/saw/drivers/web/app.py, src/saw/drivers/cli/commands/agents_cmd.py, tests/unit/test_agent_activity.py, tests/unit/test_agents_rest.py | AC-C-1, AC-C-2, AC-C-3, AC-C-4 | agent-link |

## v1.16.0 任务拆解（realtime 仪表盘，2026-09-07）
- 3 Task（1:1 Spec）：T-F-U-1（frontend agent roster+activity 仪表盘）/ T-F-U-2（frontend workflow 运行态视图）/ T-F-U-3（frontend 实时更新 polling+WS 降级）
- 2 Wave：Wave 1 T-F-U-1 / T-F-U-2（并行，Dashboard.tsx 不同区域）→ Wave 2 T-F-U-3（依赖 U-1+U-2）
- DAG U-1+U-2→U-3 无环，与 decomposition 一致
- 详见 `.csp/tasks/TASKS-DELTA-v1.16.0.md`

| task_id | spec_ref | 描述 | 类型 | 估时 | depends_on | files | acceptance | pms_module |
|---|---|---|---|---|---|---|---|---|
| T-F-U-1 | SPEC-F-U-1 | `Dashboard.tsx` 接 react-query 拉 `GET /api/v1/agents` 渲染 roster 表 + 点击展开 `GET /agents/{name}/activity` 详情；新建 `useAgents.ts` + `useAgentActivity.ts`（refetchInterval: 15000）；扩展 `AgentList.tsx`/`AgentCard.tsx`（REST roster + WS live status 覆盖 + activity_summary 列 + custom 标记 + null "—"）；新增 `AgentActivityDetail`；`types/api.ts` 新增 AgentRosterEntry/AgentActivity/ActivitySummary；新建 4 vitest 测试文件 | frontend | M | — | web/src/pages/Dashboard.tsx, web/src/components/dashboard/AgentList.tsx, web/src/components/dashboard/AgentCard.tsx, web/src/hooks/useAgents.ts, web/src/hooks/useAgentActivity.ts, web/src/types/api.ts, web/src/lib/api.ts, web/tests/test_agent_roster_render.test.tsx, web/tests/test_agent_activity_detail.test.tsx, web/tests/test_agent_activity_null.test.tsx, web/tests/test_agent_activity_404.test.tsx | AC-D-1, AC-D-2, AC-D-3, AC-D-4 | dashboard |
| T-F-U-2 | SPEC-F-U-2 | `Dashboard.tsx` 新增 `WorkflowRuntimeSection`；新建 `WorkflowList.tsx`（列表表格 + running 置顶 + 空态 + 5xx 错误条 + live 标记）+ `WorkflowRow.tsx`（status badge + steps progress + 点击展开）；新建 `useWorkflows.ts` + `useWorkflowStatus.ts`（refetchInterval: 15000）；`types/api.ts` 新增 WorkflowExecution/WorkflowListResponse/WorkflowStatusDetail/WorkflowStep；新建 3 vitest 测试文件 | frontend | M | — | web/src/pages/Dashboard.tsx, web/src/components/dashboard/WorkflowList.tsx, web/src/components/dashboard/WorkflowRow.tsx, web/src/hooks/useWorkflows.ts, web/src/hooks/useWorkflowStatus.ts, web/src/types/api.ts, web/src/lib/api.ts, web/tests/test_workflow_list_render.test.tsx, web/tests/test_workflow_running_top.test.tsx, web/tests/test_workflow_ws_update.test.tsx | AC-D-5, AC-D-6, AC-D-7 | dashboard |
| T-F-U-3 | SPEC-F-U-3 | `useWebSocket.ts` 扩展（agent_status/workflow_progress/onopen 追加 invalidateQueries(['workflows'])）；`Dashboard.tsx` 新增 polling 失败计数器（useRef + 3 次阈值）+ 降级横幅（3 种状态）+ 手动刷新按钮；`ConnectionStatus.tsx` 扩展降级状态；复用 dashboardStore + useAgents/useWorkflows；新建 1 vitest 测试文件 | frontend | M | T-F-U-1, T-F-U-2 | web/src/hooks/useWebSocket.ts, web/src/pages/Dashboard.tsx, web/src/components/dashboard/ConnectionStatus.tsx, web/src/stores/dashboardStore.ts, web/tests/test_ws_disconnect_polling_degraded.test.tsx | AC-D-8 | dashboard |

## v1.17.0 任务拆解（desktop 完成 v4.4，2026-09-07）
- 4 Task（1:1 Spec）：T-F-V-1（infra 版本 bump + 配置收敛）/ T-F-V-2（frontend web 仪表盘集成验证）/ T-F-V-3（infra tauri build 验证）/ T-F-V-4（backend-logic 后端协同 + 端口收敛）
- 2 Wave：Wave 1 T-F-V-1（版本 bump + 配置收敛先行）→ Wave 2 T-F-V-2/V-3/V-4（全并行）
- DAG V-1→{V-2,V-3,V-4} 无环，与 decomposition 一致
- 详见 `.csp/tasks/TASKS-DELTA-v1.17.0.md`

| task_id | spec_ref | 描述 | 类型 | 估时 | depends_on | files | acceptance | pms_module |
|---|---|---|---|---|---|---|---|---|
| T-F-V-1 | SPEC-F-V-1 | 4 文件版本号 0.1.0→1.0.0（desktop/package.json + tauri.conf.json + Cargo.toml + web/package.json）+ tauri.conf.json 15 项配置一致性审查确认无废弃字段；新建 test_version_consistency.py + test_tauri_config_consistency.py | infra | S | — | desktop/package.json, desktop/src-tauri/tauri.conf.json, desktop/src-tauri/Cargo.toml, web/package.json, tests/unit/test_version_consistency.py, tests/unit/test_tauri_config_consistency.py | AC-V-1, AC-V-2 | desktop |
| T-F-V-2 | SPEC-F-V-2 | 验证 desktop 加载 v1.16.0 仪表盘构建产出：frontendDist 路径解析 + web/dist/index.html 存在性 + beforeBuildCommand/beforeDevCommand 构建链验证 + @tauri-apps/api 集成验证 + devUrl 指向 vite；新建 test_web_dist_integration.py + test_web_dev_integration.py | frontend | M | T-F-V-1 | desktop/src-tauri/tauri.conf.json, web/dist/index.html, web/package.json, tests/unit/test_web_dist_integration.py, tests/unit/test_web_dev_integration.py | AC-W-1, AC-W-2 | desktop |
| T-F-V-3 | SPEC-F-V-3 | tauri build 验证：beforeBuildCommand→cargo build --release（8 插件+16 IPC+release profile）→bundle 产出原生包；新建 test_tauri_build_smoke.py（skipif no cargo）+ test_bundle_targets_config.py | infra | L | T-F-V-1 | desktop/src-tauri/tauri.conf.json, desktop/src-tauri/Cargo.toml, desktop/src-tauri/Cargo.lock, desktop/src-tauri/src/main.rs, tests/unit/test_tauri_build_smoke.py, tests/unit/test_bundle_targets_config.py | AC-B-1, AC-B-2 | desktop |
| T-F-V-4 | SPEC-F-V-4 | 端口收敛 vite proxy 8080→8000 + CORS 扩展添加 localhost:5173（web_cmd.py + app.py）+ prod 模式 VITE_API_BASE_URL/VITE_WS_URL 直连；新建 test_port_convergence.py + test_prod_backend_connection.py + test_cors_expansion.py | backend-logic | M | T-F-V-1 | web/vite.config.ts, src/saw/drivers/cli/commands/web_cmd.py, src/saw/drivers/web/app.py, web/src/lib/api.ts, web/src/hooks/useWebSocket.ts, tests/unit/test_port_convergence.py, tests/unit/test_prod_backend_connection.py, tests/unit/test_cors_expansion.py | AC-C-1, AC-C-2, AC-C-3 | desktop |
