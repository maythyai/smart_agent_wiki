# Wave Plan — 并行波次计划

> 3 Wave，镜像 decomposition 波次。共享资源（ci.yml）跨 Wave 串行追加，不并行写。

> **进度（2026-09-03）**：Wave 1 ✅ done（10/10 Task，M1 基础硬化就绪，1853 tests green）。Wave 2/3 留下一周期。

## Wave 1 — 基础层（10 Task，全并行）
| task_id | 描述 | 类型 | 里程碑 |
|---|---|---|---|
| T-F-A-1-1 | 冒烟骨架 | backend-cli | 冒烟可用 |
| T-F-B-1-1 | 宣称 diff | infra-script | 一致性可测 |
| T-F-C-1-1 | 权限矩阵 | test-security | 0 裸路由 |
| T-F-C-2-1 | receipt 闭环 | backend-security | receipt 链 |
| T-F-C-3-1 | 限流双轨 | test-security | 429 生效 |
| T-F-C-4-1 | URL 守卫 | test-security | 守卫覆盖 |
| T-F-C-5-1 | token 同源 [TBD] | backend-security | 后端统一核验 |
| T-F-D-1-1 | logger 收敛 | backend | 统一 logger |
| T-F-D-3-1 | health+JSON | backend | 健康真实 |
| T-F-E-1-1 | coverage 基线 [TBD] | infra-ci | 基线数值 |

## Wave 2 — 核心业务（7 Task）
| task_id | 描述 | 依赖 | 可并行性 |
|---|---|---|---|
| T-F-A-2-1 | ingest+compile 冒烟 | A1 | A2/A3/A4 并行 |
| T-F-A-3-1 | query 冒烟 | A1 | 同上 |
| T-F-A-4-1 | govern+learn 冒烟 | A1 | 同上 |
| T-F-B-2-1 | 能力清单 | B1 | 独立 |
| T-F-B-3-1 | 文档修正 | B1 | 独立 |
| T-F-D-2-1 | trace 贯穿 | D1 | 独立 |
| T-F-E-2-1 | coverage 门禁 | E1 | 独立 |

## Wave 3 — 集成/增强（3 Task）
| task_id | 描述 | 依赖 | 里程碑 |
|---|---|---|---|
| T-F-A-5-1 | 离线 fallback 冒烟 | A2,A3,A4 | 离线可用 |
| T-F-A-6-1 | CI smoke job | A5 | CI 守卫 |
| T-F-E-3-1 | CI 集成 | A6,E2 | 全 CI 闭环 |

## 共享资源串行
- `.github/workflows/ci.yml`：T-F-A-6-1（smoke job）→ T-F-E-2-1（coverage gate）→ T-F-E-3-1（集成）串行追加，禁并行写同文件。

## 里程碑
- M1（Wave 1 完成）：基础硬化就绪（安全/可观测/冒烟骨架/基线）。
- M2（Wave 2 完成）：核心链路冒烟全绿 + 宣称一致。
- M3（Wave 3 完成）：CI 全闭环 + 离线可用 → 05 可交付。

---

# v1.3.0 波次（硬化尾巴 + 技术债，2026-09-03）

> 源自 PRD-hardening-tail-v1.3.0 + 02 delta。Wave 2/3 Task 沿用既有（spec 已就绪），加 F-debt 3 Task。

## v1.3.0 Wave 2 — 核心业务 + docs（并行）
| task_id | 描述 | 类型 | 并行性 |
|---|---|---|---|
| T-F-A-2-1 | ingest+compile 冒烟 | test | A2/A3/A4 并行 |
| T-F-A-3-1 | query 冒烟 | test | 同上 |
| T-F-A-4-1 | govern+learn 冒烟 | test | 同上 |
| T-F-B-2-1 | 能力清单 CAPABILITIES.md | infra-script | 独立 |
| T-F-B-3-1 | 文档修正 | doc | 独立 |
| T-F-D-2-1 | trace_id 贯穿 | backend | 独立 |
| T-F-E-2-1 | coverage 门禁≥80% | infra-ci | 独立 |
| T-F-Z-2-1 | roadmap narrative 重写 | doc | 独立（docs，与 src 不冲突）|
| T-F-Z-3-1 | v1.2.0 行为变更迁移文档 | doc | 独立（docs）|

## v1.3.0 Wave 3 — 集成 + ruff 收口（串行末位）
| task_id | 描述 | 依赖 | 里程碑 |
|---|---|---|---|
| T-F-A-5-1 | 离线 fallback 冒烟 | A2,A3,A4 | 离线可用 |
| T-F-A-6-1 | CI smoke job | A5 | CI 守卫 |
| T-F-E-3-1 | CI 集成 | A6,E2 | 全 CI 闭环 |
| **T-F-Z-1-1** | **ruff baseline 收口** | **A2/A3/A4/D2 后串行** | **lint 门禁就绪** |

## v1.3.0 共享资源串行
- `.github/workflows/ci.yml`：A6→E2→E3 串行追加（沿用既有约束）。
- **F-Z-1 ruff 是共享资源**（pyproject + 全 src）：必须在所有 src 改动（A2/A3/A4/D2）合并后串行执行，禁并行。

## v1.3.0 里程碑
- M2（Wave 2）：核心链路冒烟全绿 + 宣称一致 + trace 贯穿 + coverage 门禁 + debt docs。
- M3（Wave 3）：CI 全闭环 + 离线可用 + ruff lint 门禁 → v1.3.0 可交付。

---

# v1.4.0 波次（平台化与团队协作，2026-09-03）

> 源自 PRD-platform-team-v1.4.0 + 02 delta + ADR-005。platform-team 新域。

## v1.4.0 Wave 1 — platform + debt（并行）
| task_id | 描述 | 类型 | 并行性 |
|---|---|---|---|
| T-F-P-1-1 | RBAC 深化（Cedar 热加载 + e2e） | backend | 独立（auth/）|
| T-F-P-2-1 | 团队部署（docker-compose.prod） | infra | 独立（docker/）|
| T-F-P-3-1 | 可观测闭环（saw health + audit） | backend-cli | 独立（cli/commands/）|
| T-F-Z-5-1 | heavy-SDK importorskip | test | 独立（tests/）|

## v1.4.0 Wave 2 — workspace 隔离（migration v8 串行）
| task_id | 描述 | 依赖 | 里程碑 |
|---|---|---|---|
| T-F-P-4-1 | 多 workspace 隔离（schema 前缀 + v8 + 授权绑定） | P-1 | 多团队共存 |

## v1.4.0 Wave 3 — ruff 收口续（串行末位）
| task_id | 描述 | 依赖 | 里程碑 |
|---|---|---|---|
| T-F-Z-4-1 | ruff F401/F841 收口 | P-1/P-3/P-4 后串行 | lint 门禁加严 |

## v1.4.0 共享资源串行
- migration v8（F-P-4 workspace_id 列）：Wave 2 串行。
- ruff F401/F841 全库修（F-Z-4）：Wave 3 串行末位，所有 src 改动后。

## v1.4.0 里程碑
- M4（Wave 1）：platform 基座（RBAC/deploy/observability CLI）+ heavy-SDK 优雅跳过。
- M5（Wave 2）：多 workspace 隔离可用 → 多团队共存。
- M6（Wave 3）：ruff F401/F841 启用 → lint 门禁加严 → v1.4.0 可交付。
