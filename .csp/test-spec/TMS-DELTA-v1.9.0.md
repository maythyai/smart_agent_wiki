# TMS Delta — v1.9.0（2026-09-04）

> 03 测试规约 delta。agent-viz 新能力。增量用例。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-WF-3（workflow list 最近运行） | F-M-1 | `tests/unit/test_workflow_cmd.py`（扩）：seed 2 行 → list 含两行 + 排序 | [TBD-impl] |
| AC-AG-2（6 角色表） | F-M-2 | `tests/unit/test_agents_cmd.py`（新建）：invoke → 含 6 角色 + Guardian rule | [TBD-impl] |
| AC-API-1（6 角色 JSON） | F-M-3 | `tests/unit/test_agents_api.py`（新建）：TestClient GET /api/v1/agents → 6 角色 | [TBD-impl] |

## 约定
- F-M-1 用 in-memory DB + seed workflow_executions 行（apply_migrations v4）。
- F-M-2/F-M-3 用 build_default_agents 静态 roster（无 LLM、无 DB）。
- 无 ADR（复用基建，无架构变更）。
