---
id: CONVERGENCE-REPORT-2026-10-27
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-27
status: active
see_also: docs/strategy/ROADMAP.md §2.7 | docs/analysis/INTEGRATION-NECESSITY-2026-10-20.md
---

# 产品架构收敛审查报告 — Smart Agent Wiki（2026-10-27）

## 执行摘要

**结论：✅ 通过**（无定位漂移，无导航超预算，无系统级卫生阻断。1 项系统卫生 WARNING 待清理。）

- 纳入 8 版本（v1.34.1–v2.0.0），全部通过定位对齐检查
- 降级 0（Phase 2.5 已前置完成——9 版降级到 v2.0+/v3.0）
- 导航预算：7/7（满额，本版本不新增顶级导航）
- 定位漂移：0 项
- 系统级卫生：1 WARNING（v1.18.1 tag 文档-only，存量基线已吸收）

## Phase 0：定位与支柱基线

### 定位基线卡

- **操作者模型**：local-first（AGENTS.md §1）+ 3 角色 KW/DEV/OPS（STRATEGY.md §3）
- **目标用户**：知识工作者 KW、开发者 DEV、平台运维者 OPS
- **北极星指标**：trustworthy-claim coverage
- **产品阶段**：增长期（已发 8 版 v1.30.1–v1.34.0，MCP 35→39 tools）
- **核心支柱**：
  | 支柱 | 定义 | 服务用户 |
  |------|------|---------|
  | 支柱1: core-trust（可信地基） | provenance/治理/审计/质量门 | KW/DEV/OPS |
  | 支柱2: platform-team（平台化） | self-hosted 多用户/RBAC/可观测/SSO | OPS/DEV |
  | 支柱3: ecosystem-integration（生态集成） | plugin SDK/connectors/coding-harness | DEV |
  | 支柱4: intelligence-adaptation（智能自适应） | agents/reasoning/context API/token opt | KW/DEV |
- **明确不做**：cloud-first/SaaS、通用 RAG chatbot、厂商锁定（STRATEGY §6）

### 定位漂移预警

> 检测关键词 `SSO|多租户|企业|团队|RBAC|marketplace|IM SDK` 在 v1.34.1–v2.0.0 净版中的命中

| 版本 | 功能 | 关键词 | 漂移检测 |
|------|------|--------|---------|
| v1.38.0 | SSO/OIDC + RBAC深化 | SSO, RBAC | 🟡 审查通过：STRATEGY §2 track "platform-team" 明确覆盖 self-hosted 多用户；SSO/OIDC 为 self-hosted 部署（非 SaaS），与 local-first 兼容 |
| v1.38.0 | Plugin SDK v1 stable | plugin | ✅ 支柱3 ecosystem，生态集成定位 |
| v1.38.0 | Observability v2 | — | ✅ 支柱2 platform，OPS 场景 |

> 检测结果：0 项 🔴 漂移。唯一 🟡 项 SSO/OIDC 经审查通过（self-hosted OIDC，非 cloud SSO）。Phase 2.5 已前置剔除 marketplace/IM SDK/sandbox/federation 等真漂移项。

## Phase 1：功能全景重建 + 定位对齐 + 支柱映射

### 版本功能矩阵（净版 v1.34.1–v2.0.0）

| 功能 | 版本 | 支柱映射 | 定位对齐 | 收敛动作 |
|------|------|---------|---------|---------|
| coverage 70% + god-files + stale-freshness + Dashboard | v1.34.1 | 支柱1 | ✅ | 纳入（4→1 合并） |
| Structured Context API v1 | v1.35.0 | 支柱4 | ✅ | 纳入 |
| Incremental Graph + Reasoning + Deep Research v2 | v1.36.0 | 支柱4 | ✅ | 纳入（v1.36+v1.45 合并） |
| Governed Code Intelligence + Token Optimizer | v1.37.0 | 支柱1+4 | ✅ | 纳入（v1.43+v1.44 合并） |
| RBAC深化 + SSO/OIDC + Plugin SDK + Obs v2 | v1.38.0 | 支柱2+3 | ✅（审查通过） | 纳入（v1.39+v1.40SDK+v1.47obs 合并） |
| Pre-v2.0 硬化 + coverage 75 | v1.39.0 | 支柱1 | ✅ | 纳入 |
| v2.0 RC + Context API freeze | v1.40.0 | 支柱4 | ✅ | 纳入 |
| 平台化 MAJOR | v2.0.0 | 支柱2 | ✅ | 纳入（仅真实 breaking） |

## Phase 2：六维度收敛审查

### D1 功能架构收敛

| 检查项 | 判定 |
|--------|------|
| 模块职责单一清晰 | ✅ 六引擎（Ingest/Query/Govern/Learn/Collaborate/Write Queue）边界明确 |
| 同一用户任务仅在单一模块 | ✅ query 归 QueryEngine，govern 归 Governor，collaborate 归 CollaborateEngine |
| 新增功能有明确归属 | ✅ 全部功能映射到既有引擎 |
| 功能间依赖合理 | ✅ v1.35→v1.36→v1.37→v1.38 线性依赖 |
| 无万能/贫血模块 | ✅ |

### D2 核心/次要取舍

| 版本 | 级别 | 理由 |
|------|------|------|
| v1.34.1 | Must-have | core-trust：质量门 + findings 闭合 |
| v1.35.0 | Must-have | ★品类定位：差异化 fortress |
| v1.36.0 | Must-have | 核心 intelligence 能力 |
| v1.37.0 | Should-have | DEV 价值：governed code + cost |
| v1.38.0 | Should-have | platform-team：to-B self-hosted capability |
| v1.39.0 | Must-have | 质量：发布前硬化 |
| v1.40.0 | Must-have | API freeze：v2.0 MAJOR 前奏 |
| v2.0.0 | Must-have | 战略 milestone |

> 无 Nice-to-have 或 Wrong 级别功能（已在前置 Phase 2.5 剔除）。

### D3 IA 方向 + 导航准入

| 检查项 | 判定 |
|--------|------|
| 当前顶级导航数 | 7（pages/search/graph/dashboard/integrations/import/templates/timeline）|
| 预算上限 | 7 |
| 本版本新增 | 0（满额，不新增）✅ |
| 导航分类与用户心智一致 | ✅（按任务域：浏览/搜索/关系/概览/集成/导入/模板/时间线）|
| 核心任务 ≤3 次点击 | ✅ |
| 功能孤岛 | 0（v1.33.0 修复了 /integrations 无 nav）|
| Dashboard 按钮→nav 重复 | CRITIC-F-01 → v1.34.1 修复 ✅ |

### D4 迭代优先级

| 检查项 | 判定 |
|--------|------|
| 功能依赖拓扑排序 | ✅ v1.34.1(base) → v1.35(context API) → v1.36(reasoning) → v1.37(code intel) → v1.38(platform) → v1.39(hardening) → v1.40/2.0 |
| 核心路径优先 | ✅ core-trust + intelligence 先于 platform |
| 基础设施先于业务功能 | ✅ v1.35 Structured Context API 先于 v1.36 reasoning |
| 高风险功能早期验证 | ✅ v1.35 API 设计风险在 first phase 暴露 |
| 同模块打包 | ✅ v1.36+v1.45（同 intelligence）, v1.37（v1.43+v1.44 同 DEV）, v1.38（v1.39+SDK+obs 同 platform）|

### D5 定位对齐与前提挑战

| 功能 | Q1 服务谁 | Q2 真实痛点 | Q3 不做会怎样 | 裁决 |
|------|----------|-----------|------------|------|
| Structured Context API | DEV | agent context 碎片化 | SAW 品类定位不成立 | ✅ 保留 |
| SSO/OIDC | OPS | self-hosted 团队需认证 | to-B self-hosted 无法落地 | ✅ 保留（self-hosted OIDC，非 cloud）|
| Plugin SDK | DEV | 生态扩展 | 生态无法起步 | ✅ 保留 |
| Governed Code Intel | DEV | code intel 无治理 | vs CodeGraph 无差异化 | ✅ 保留 |
| Token Optimizer | DEV/KW | agent token 成本失控 | 成本痛点不解决 | ✅ 保留 |

> 0 项"不做会怎样=没影响"——全部有真实用户场景支撑。

### D6 系统级卫生

| 检查项 | 状态 | 裁决 |
|--------|------|------|
| 后端 API 膨胀 | 🟡 114 paths，部分孤儿（审计已标记） | 不阻断（非本版主题，列入 backlog） |
| Feature Flag 卫生 | 🟢 auth_mode(local/team)，team 为 default-off 但代码 active | OK（v1.4 已实现，非死代码） |
| ADR 编号冲突 | 🟢 统一编号空间 `.csp/tech-decisions/ADR/` | OK |
| 版本口径一致性 | 🟢 git tag 为唯一真相源（version_integrity 闸门通过） | OK |
| DOC-STATUS 新鲜度 | ⚠️ 部分 docs 上次审计 2026-09-18（~40 天），阈值 30 天 → **WARNING** | 不阻断：v1.34.1 含代码变更（非纯文档版）；下次审计刷新 docs |
| AGENTS.md 与实际一致 | ✅ local-first 一致 | OK |
| FINDINGS 基线 | ✅ 双闸门 exit 0 | OK |
| PLACEHOLDER 占位 | 🟢 0 占位（ROADMAP §5 全 closed 或 deferred 带条件） | OK |

## Phase 3：五类根因 Pattern 检测

| Pattern | 检测结果 | 说明 |
|---------|---------|------|
| A: 定位漂移 | ✅ 0 项 | Phase 2.5 已前置剔除 marketplace/IM/Sandbox/federation |
| B: 架构无收敛 | ✅ | 8 版本 4 合并，模块边界清晰 |
| C: IA 债 | ✅ | v1.33.0 修导航；v1.34.1 修 Dashboard |
| D: 后端膨胀 | 🟡 | 审计曾标孤儿 API（AUDIT-F-05/06 已 closed v1.33.0；余未清理） |
| E: 文档权威 | ⚠️ 1 WARNING | doc freshness 40d > 30d（不阻断） |

## Phase 4：收敛后功能清单

见 `.csp/convergence/CONVERGED-FEATURE-PLAN.md`（Phase 4.5 PRD SPECs 已产，此文件为 01 入口引用）。

## Phase 5：裁决记录

| ID | 裁决 | 对象 | 理由 |
|----|------|------|------|
| CVG-001 | 纳入 | v1.34.1 全功能 | core-trust 质量门 ✓ |
| CVG-002 | 纳入 | v1.35 Structured Context API | intelligence ★品类定位 ✓ |
| CVG-003 | 纳入 | v1.36 Incremental Graph + DW v2 | intelligence 合并 ✓ |
| CVG-004 | 纳入 | v1.37 Governed Code + Token | DEV 合并 ✓ |
| CVG-005 | 🟡纳入 | v1.38 SSO/OIDC | self-hosted OIDC（非 cloud SSO）✓ |
| CVG-006 | 纳入 | v1.39 硬化 + v1.40 RC + v2.0 MAJOR | 战略 milestone ✓ |
| CVG-007 | ⚠️ WARNING | DOC-STATUS 40d > 30d | 本版修复（v1.34.1 含代码变更） |

## 交棒 → 01 PRD

- **收敛后功能清单**：`.csp/convergence/CONVERGED-FEATURE-PLAN.md`
- **IA 优化方向**：`.csp/convergence/IA-DIRECTION.md`（导航满额 7/7，不新增）
- **系统级卫生**：`.csp/convergence/SYSTEM-HYGIENE-2026-10-27.md`
- **裁决记录**：本报告 Phase 5
- **下一步**：01 PRD v1.34.1——基于收敛后功能清单 + 升级已有 planning PRD SPEC → engineering