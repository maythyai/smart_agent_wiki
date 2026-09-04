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
