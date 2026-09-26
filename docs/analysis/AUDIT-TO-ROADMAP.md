# Audit → Roadmap 交棒 — Smart Agent Wiki @ v1.30.0 (Step 5)

> 2026-09-18. 聚合审计 findings → roadmap 主题候选 + 交棒。来源: `docs/audit/PRODUCT-AUDIT.md`（AUDIT-F/CRITIC-F/GAP-F/BLOCKED）。过 Phase 2.5 集成必要性审视。

## 快速修复通道（跳 roadmap/01，直发 04→05→06 PATCH）
> P0 + `快速修复=true` 项走 v1.30.1 PATCH（不另开 MINOR）。

| finding | 修复 | 版本 |
|---|---|---|
| AUDIT-F-02 | 更新 test_mcp_tools.py expected_tools +1 + README/manifest/test 三处对齐真实工具数(35) | v1.30.1 (PATCH) |
| AUDIT-F-07 | App.tsx 顶部 nav 增 Integrations NavLink | v1.30.1 |
| AUDIT-F-09 | /integrations 图标按钮补 aria-label | v1.30.1 |
| AUDIT-F-10 | /graph 空状态加 CTA（Import/新建页面） | v1.30.1 |

## 集成必要性审视（Phase 2.5）——是否进既有 roadmap 版本？

| finding | 进哪个既有版本 | 理由 |
|---|---|---|
| AUDIT-F-05 (saw web 挂 SPA) | **v1.33.0**（Playwright E2E + Desktop） | saw web 服务 SPA 是 E2E gate 前置；v1.33 本就做 Playwright/desktop，自然含 SPA 挂载。**提升优先级至 P1**（解 E2E-BLOCKED-01） |
| AUDIT-F-06 (vite proxy 配置化) | v1.33.0 | 与 SPA 挂载同批：proxy target 走 env/config，解 vLLM 冲突 |
| AUDIT-F-03 (wiki 索引 YAML 韧性) | v1.34.0（性能硬化 II）或 v1.31.0 | 韧性属 core-trust；可并入 v1.31 Provenance（同治理主线） |
| AUDIT-F-01 (god-files) | v1.34.0（性能硬化 II，含 refactor） | compiler.py/engine.py 拆分续 v1.19 S4 |
| AUDIT-F-04 (coverage 70%) | v1.34.0 | 同 perf 硬化 batch |
| AUDIT-F-08 (404→200) | v1.33.0（前端硬化同批） | 前端 correctness |
| CRITIC-F-01 + GAP-F-02 (Dashboard 状态卡) | v1.35.0（Structured Context API v1） | dashboard 改造接 stats/workflows/contradictions——与 Context API 同批 |
| CRITIC-F-04 + GAP-F-01/03/05/06/07 (空状态/列表增强) | v1.33.0 批 + UnifiedEmptyState 组件 | 前端硬化批 |

## 新增 roadmap 主题候选（未在既有 v1.31–v2.2 覆盖）
- **v1.30.1** (PATCH) — audit 快速修复批（AUDIT-F-02/07/09/10）。**新增**：不在既有序列，作为 fix 批 PATCH tag。
- 不新增战略级版本——audit findings 全部可并入既有 v1.31–v1.35 主线，无需开新主题。

## 交棒动作
1. **06 release**：v1.30.1 PATCH tag（快速修复批），FEATURES.md 标 ✅。
2. **ROADMAP 更新**：v1.33.0 增 "saw web 挂 SPA + Playwright E2E + proxy 配置化"（AUDIT-F-05/06/08），优先级 P1（解 E2E-BLOCKED-01）；v1.34.0 增 god-files 拆分续 + coverage 70；v1.35.0 增 Dashboard 状态卡。
3. **07 复盘**：findings 回流（AUDIT-F-02 已快速修复→closed；AUDIT-F-05/06 进 v1.33；余进 v1.34/1.35）。
4. **E2E-BLOCKED-01**：解除条件=v1.33 saw web 挂 SPA；解除后重跑数据依赖 E2E。

## 与既有 roadmap 的对齐
- v1.31.0 (Provenance API) ← 可并入 AUDIT-F-03（wiki 索引韧性，core-trust 同主线）。
- v1.33.0 (Playwright/desktop) ← 升级为 "saw web SPA + Playwright + Desktop 签名"（AUDIT-F-05/06/08/07/09/10 快速修复外的部分）。
- v1.34.0 (ANN/coverage) ← 并入 AUDIT-F-01 god-files + AUDIT-F-04 coverage。
- v1.35.0 (Structured Context API) ← 并入 CRITIC-F-01 Dashboard 状态卡。
