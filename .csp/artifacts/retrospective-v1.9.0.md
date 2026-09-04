# 复盘 — v1.9.0 Agent & Workflow 可视化（2026-09-04）

> 07 闭环校验。findings 回流下一轮 01。

## 闭环校验结论：✅ 通过

| 链路 | 状态 | 证据 |
|---|---|---|
| PRD → Spec | ✅ | PRD-agent-viz-v1.9.0 Approved；3 SPEC 1:1（无 ADR，复用基建）|
| Spec → Task | ✅ | WBS 3 Task（T-F-M-1..3）覆盖 3 Feature |
| Task → commit | ✅ | 6140f65（impl + tests + DEV-LOG）|
| AC → 测试 | ✅ | AC-WF-3(workflow list) / AC-AG-2(agents 6 角色) / AC-API-1(/agents JSON) |
| commit → tag | ✅ | v1.9.0 annotated @ 246f3d4 |
| 测试/lint | ✅ | 1987 passed/3 skipped；ruff src/+tests/ 0 errors；smoke 6/6 |
| 构建 | ✅ | wheel smart_agent_wiki-1.9.0 |

## v1.9.0 度量
- 3 Feature done（新能力：workflow list + agents CLI + agents REST）
- 新增测试 4（workflow list 2 + agents CLI 1 + agents API 1）
- 全量 1987 passed（+4 vs v1.8.0）；coverage 64.2%（未变——CLI 薄 wiring）；fail_under=64 持
- 续新能力第二轮：复用 workflow 基建 + build_default_agents，无新引擎

## Findings（回流下一轮）

### M1 — embedding 语义搜索仍 defer [中]
本轮仍 defer（heavy SDK sentence-transformers，硬约定 #12 须用户确认装；本环境无法验证）。v4.2 留尾。
- **回流 01/决策**：若用户确认装 `[learn]` extra（含 sentence-transformers），下一轮可开 embedding 语义搜索。

### M2 — agent "最近活动"未聚合 [低]
roster 是静态（name/model_tier/tools），无"最近活动/调用次数"。需 event bus 聚合 workflow_step 事件。
- **回流 03/05**：后续可加 `GET /api/v1/agents/{name}/activity`（聚合 WorkflowStep 事件）。

### M3 — CLI workflow list vs REST /workflows 语义双重 [低]
CLI list = durable DB 历史；REST /workflows = in-memory live。两者互补但语义双重，须文档明确（已在本轮 PRD/DEV-LOG 标注）。
- **回流 03**：可统一 REST /workflows 也读 DB（merge live + durable）以消歧；但改既有行为，留后续。

## 下游衔接 → v2.0.0（新一轮 01）
- v2.0.0 是 major 版本节点。候选：embedding 语义搜索（须用户确认装 SDK）/ realtime agent 仪表盘（v4.3 完整前端）/ desktop 完成（v4.4）/ 自定义 agent 角色注册（v1.5.0 留 v2.0）。
- 累计 v1.5.0–v1.9.0 五轮：3 轮债务收口（workspace 三闭环）+ 2 轮新能力（smart linking + agent 可视化）。
- K1（coverage 65）/ K2（per-request ws）/ L1-L3 续留 finding。
