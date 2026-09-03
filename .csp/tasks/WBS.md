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
