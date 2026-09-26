---
id: ARCHIVE-MANIFEST-v1.30.1
milestone: v1.30.1
release_type: PATCH
tag: v1.30.1
commit: d4389fc
released: 2026-09-18
canonical_version: 1.30.1
---

# Archive Manifest — v1.30.1 (audit 快速修复批 PATCH)

## Release
- tag: `v1.30.1` (annotated, immutable, pushed origin)
- commit: `d4389fc release: v1.30.1 — audit 快速修复批 PATCH`
- GitHub Release: https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.30.1
- assets: `smart_agent_wiki-1.30.1-py3-none-any.whl` + `smart_agent_wiki-1.30.1.tar.gz`

## Findings closed (4)
- AUDIT-F-02 [P0] MCP 工具数断言（34→35, saw_deep_research）+ README 三处对齐
- AUDIT-F-07 [/integrations nav] App.tsx 增 NavLink
- AUDIT-F-09 [/integrations a11y] Refresh 按钮 aria-label
- AUDIT-F-10 [/graph 空态] CTA Import/Browse pages

## Gate
- pytest 2399 pass / 7 skip / 0 fail (+1)
- coverage 68.42% (gate 67 ✓)
- ruff 0; tsc clean; vitest 64 pass
- bump: 1.30.0 → 1.30.1 (pyproject + VERSION, PATCH; desktop/web 保持 1.0.0)

## Findings 折入后续版本（未闭合，显式计入下一版 01 入口）
- AUDIT-F-03 (wiki 索引 YAML 韧性) → v1.31.0
- AUDIT-F-05/06 (saw web 挂 SPA + proxy 配置化) + AUDIT-F-08 (404→200) → v1.33.0
- AUDIT-F-01/04 (god-files + coverage 70) → v1.34.0
- CRITIC-F-01 (Dashboard 状态卡) → v1.35.0
- E2E-BLOCKED-01 (数据依赖 E2E) → 解除条件 v1.33 saw web 挂 SPA

## 07 retro
- 见 `.csp/artifacts/retrospective-v1.30.1.md`
