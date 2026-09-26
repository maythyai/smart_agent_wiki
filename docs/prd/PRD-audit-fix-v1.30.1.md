---
id: PRD-audit-fix-v1.30.1
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-18
status: approved
roadmap_ref: ROADMAP
target_version: v1.30.1
type: fix-batch
see_also: .csp/audit/AUDIT-FINDINGS-v1.30.0.json | docs/analysis/AUDIT-TO-ROADMAP.md
---

# PRD — v1.30.1 audit 快速修复批

> PATCH（fix 攒批，不开 MINOR）。源自 v1.30.0 全链路审计（`.csp/audit/AUDIT-FINDINGS-v1.30.0.json`）中 `快速修复=true` 项。每条 finding 已有证据 + fix hint，本 PRD 仅定义验收。

## 背景
v1.30.0 审计发现 1 P0 测试失败 + 3 P2/P3 可快速整改项。本批闭合之，解 06 gate（test 失败阻 CI）。

## 范围（4 项 fix）
| finding | 严重度 | 修复 | 验收 |
|---|---|---|---|
| AUDIT-F-02 | P0 | test_mcp_tools.py expected_tools 加 saw_deep_research（34→35）+ README MCP 工具数 64+/56+→35 对齐 | pytest 0 failed；README 三处一致(35) |
| AUDIT-F-07 | P3 | App.tsx 顶部 nav 增 Integrations NavLink | /integrations 经 nav 可达 |
| AUDIT-F-09 | P2 | Integrations.tsx Refresh 按钮补 aria-label="Refresh" | 图标按钮有可访问名 |
| AUDIT-F-10 | P3 | Graph.tsx 空态加 CTA（Import / 新建页面 Link） | 空态有动作入口 |

## 非目标（折入后续版本，见 AUDIT-TO-ROADMAP）
- AUDIT-F-05/06（saw web 挂 SPA + proxy 配置化）→ v1.33.0
- AUDIT-F-01/04（god-files + coverage 70）→ v1.34.0
- AUDIT-F-03（wiki 索引韧性）→ v1.31.0
- AUDIT-F-08（404→200）→ v1.33.0
- CRITIC-F-01（Dashboard 状态卡）→ v1.35.0

## 成功指标
- pytest 0 failed / ruff 0 / coverage 不回归（≥68%）。
- 4 findings → closed；ROADMAP/FEATURES v1.30.1 标 ✅ shipped。

## 留尾
- 无 deferred 项入本批（全 4 项本版交付）。
- 余 audit findings 显式折入后续版本（上表），不"下轮再补"。
