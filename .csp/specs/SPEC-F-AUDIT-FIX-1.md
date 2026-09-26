---
id: SPEC-F-AUDIT-FIX-1
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-18
status: approved
prd_ref: PRD-audit-fix-v1.30.1
target_version: v1.30.1
---

# SPEC — v1.30.1 audit 快速修复批（详细）

## F-AUDIT-FIX-1: MCP 工具数断言修复（AUDIT-F-02）
**根因**: v1.30.0 新增 `saw_deep_research` MCP 工具（A4 深度研究），但 `tests/unit/drivers/test_mcp_tools.py` 的 `expected_tools` 列表未同步（仍 34，实际 35）。
**改动**:
1. `tests/unit/drivers/test_mcp_tools.py` expected_tools 加 `"saw_deep_research"`（放在 v1.30 A4 注释组，与 saw_wiki_distill 等并列）。
2. README.md MCP 工具数三处对齐到 35：
   - line 9 badge `MCP-64+%20tools` → `MCP-35%20tools`
   - line 31 `56+ tools` → `35 tools`
   - line 202 `## MCP Tools (56+)` → `## MCP Tools (35)`
**AC**:
- `pytest tests/unit/drivers/test_mcp_tools.py::TestAllToolsCount::test_all_tools_registered` PASS。
- README 三处均为 35，与 `_get_tool_names_sync()` 实际一致。

## F-AUDIT-FIX-2: /integrations 顶部 nav 入口（AUDIT-F-07）
**根因**: `web/src/routes/router.tsx` 含 `/integrations` 路由，但 `web/src/App.tsx` 顶部 NavLink 仅 7 项（pages/search/graph/dashboard/import/templates/timeline），缺 Integrations。
**改动**: `web/src/App.tsx` 在 Dashboard NavLink 后插入 Integrations NavLink（同结构，`to="/integrations"`）。
**AC**:
- 顶部 nav 含 Integrations 链接，点击导航到 /integrations。
- 桌面端可见（hidden md:flex 内）。

## F-AUDIT-FIX-3: Integrations Refresh 按钮 aria-label（AUDIT-F-09）
**根因**: `web/src/pages/Integrations.tsx` System Health 区 Refresh 按钮（line 71-80）文字 `hidden sm:inline`，移动端图标按钮无 `aria-label`，可访问名为空。
**改动**: 该 `<button>` 加 `aria-label="Refresh"`。
**AC**:
- 移动端（文字隐藏）下按钮有可访问名 "Refresh"。
- 桌面端视觉不变。

## F-AUDIT-FIX-4: Graph 空态加 CTA（AUDIT-F-10）
**根因**: `web/src/pages/Graph.tsx` 空态（line 177-191）有文案 "No entities in the graph yet" + "Start by creating pages..."，但**无动作按钮**——用户无入口去 import/create。
**改动**: 在空态 `<p>` 后加两个 CTA：
- `<Link to="/import">` "Import documents" 按钮（primary）
- `<Link to="/pages">` "Browse pages" 按钮（secondary）
需 `import { Link } from 'react-router'`。
**AC**:
- 空态显示两个 CTA，分别导航到 /import 与 /pages。
- 视觉与现有 Retry 按钮风格一致。

## 测试
- 后端: `pytest tests/unit/drivers/test_mcp_tools.py -q` 全绿。
- 全量回归: `pytest tests/ -q`（0 failed）+ `ruff check .`（0）+ coverage 不回归。
- 前端: `cd web && npx tsc --noEmit`（0 err）+ `npx vitest run`（如有相关测试）。
- 无需 E2E（数据依赖 BLOCKED，结构性改动由 tsc + 单测覆盖）。
