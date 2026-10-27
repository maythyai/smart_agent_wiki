---
id: CONVERGED-FEATURE-PLAN
project: smart-agent-wiki
version: 1.0
last_updated: 2026-10-27
status: active
upstream: .csp/convergence/CONVERGENCE-REPORT-2026-10-27.md
---

# 收敛后功能清单 — Smart Agent Wiki

> 01 PRD 唯一输入（基于收敛闸门审查）。功能清单来自 ROADMAP §2.7 净版（Phase 2.5 集成必要性审视后），经 product-design-convergence 闸门审查通过。

## 定位对齐声明
- 操作者模型：local-first（AGENTS.md §1）
- 全部功能已通过定位对齐检查（0 🔴 漂移）
- 1 🟡 审查通过（v1.38.0 SSO/OIDC → self-hosted OIDC，非 cloud）

## 版本功能清单

### v1.34.1 — core-trust 硬化（Must-have）
- F1: coverage → 70%（AUDIT-F-04 partial）
- F2: god-files 拆分起步（compiler.py <600L, AUDIT-F-01）
- F3: stale-freshness contamination（v1.31.1 deferred）
- F4: Dashboard 按钮去重（CRITIC-F-01 合并）
- PRD SPEC: `docs/prd/PRD-v1.34.1-core-trust-hardening.md`（planning Draft → 01 升级 engineering）

### v1.35.0 — Structured Context API v1 ★品类定位（Must-have）
- F1: `saw_context` 统一 MCP+REST 接口
- F2: ontology 层（concept type/relations 锚定 claims）
- F3: state 层（freshness/confidence 作 query filter）
- F4: 自适应查询路由（confidence 门控）
- F5: permission 维度（RBAC workspace 过滤）
- PRD SPEC: `docs/prd/PRD-v1.35-structured-context-api.md`（planning Draft → 01 升级）

### v1.36.0 — Incremental Graph + Reasoning + Deep Research v2（Must-have）
- F1: claims 图 delta-merge 增量更新
- F2: logical-symbolic reasoner（plan/retrieve/reason）
- F3: hierarchical community report v2
- F4: Deep Research v2（多步 web+claims+reasoner→可溯源报告）
- PRD SPEC: `docs/prd/PRD-v1.36-incremental-graph-reasoning.md`（planning Draft → 01 升级）

### v1.37.0 — Governed Code Intelligence + Token Optimizer（Should-have）
- F1: tree-sitter AST zero-LLM 解析
- F2: coding-harness skills 全平台
- F3: token ledger 产品化（/api/v1/tokens + saw_tokens MCP）
- F4: context-compaction
- PRD SPEC: `docs/prd/PRD-v1.37-governed-code-intelligence.md`（planning Draft → 01 升级）

### v1.38.0 — RBAC深化 + SSO/OIDC + Plugin SDK + Observability v2（Should-have）
- PRD SPEC: [TBD]（待本版 PRD 01 阶段产出）

### v1.39.0 — Pre-v2.0 硬化（Must-have）
- PRD SPEC: [TBD]

### v1.40.0 — v2.0 RC（Must-have）
- PRD SPEC: [TBD]

### v2.0.0 — 平台化 MAJOR（Must-have）
- PRD SPEC: [TBD]

## 系统级卫生整改（本版本前置）

| 整改项 | 裁决 | 版本 |
|--------|------|------|
| DOC-STATUS 刷新（上次审计 2026-09-18，40d > 30d WARNING）| 本版本修订 docs/audit/ 相关文档 freshness | v1.34.1 同批 |

## 导航预算状态
- 当前顶级导航：7（pages/search/graph/dashboard/integrations/import/templates/timeline）
- 预算上限：7（满额）
- 本版本新增：0
- 本版本修改：Dashboard 按钮去重（v1.34.1 CRITIC-F-01）