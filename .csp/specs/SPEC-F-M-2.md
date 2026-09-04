---
id: SPEC-F-M-2
title: agent roster CLI（saw agents）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-04"
prd_ref: docs/prd/PRD-agent-viz-v1.9.0.md
pms_ref: .csp/product-spec/PMS-agent-viz.md
feature_id: F-M-2
complexity: S
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-M-2]
---

# SPEC-F-M-2: saw agents

## 实现 delta（ground 自源码）
- 新增 `drivers/cli/commands/agents_cmd.py`（Typer command），`main.py` 注册 `app.command(name="agents")(agents)`。
- `build_default_agents(llm_router=None)` → 6 角色 dict；每 agent `.name` + `.model_tier` + `._tools_allowed` + `._constraints`。
- 输出表：name / model_tier / tools_allowed / rule?(model_tier=='rule')。
- 无 DB；纯静态 roster。

## 接口契约
- `saw agents` → 6 角色表；exit 0。

## 后端逻辑
- build_default_agents(None) → 遍历 → Rich table。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-AG-2（6 角色表） | `tests/unit/test_agents_cmd.py`：invoke → 含 6 角色（Librarian/Writer/Critic/Linker/Scholar/Guardian）+ Guardian rule |

## 实现就绪度
- [x] build_default_agents 就绪
- [x] AC 覆盖 1/1
