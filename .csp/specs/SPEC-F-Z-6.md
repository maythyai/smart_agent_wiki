---
id: SPEC-F-Z-6
title: ruff F841 收口（27 死赋值手修 + 启用）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-03"
prd_ref: docs/prd/PRD-intelligence-adaptation-v1.5.0.md
pms_ref: .csp/product-spec/PMS-intelligence-adaptation.md
feature_id: F-Z-6
complexity: M
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-Z-6]
---

# SPEC-F-Z-6: F841 收口

## 实现 delta（ground 自源码）
- ruff `--select F841` 报 27 errors（src/saw，全 dead assigns w/ side-effect RHS，`pyproject.toml:89` ignore 注释已标注）。
- 逐文件手审（沿用 v1.4.0 Z-4 F401 纪律）：分类——
  - **drop-assign**（RHS 无副作用，纯死赋值）→ 删赋值行。
  - **side-effect RHS**（RHS 有 I/O/调用，须保留调用）→ 改 `x = call()` 为 `call()`（裸表达式语句）或显式 `_ =`。
  - **intentional**（如接口契约返回值）→ `# noqa: F841` 局部抑制 + 注释理由。
- 修完从 `pyproject.toml` ignore 移除 `"F841"`（启用），`ruff check src/` 0 errors。

## 接口契约
- 无新 CLI；`pyproject.toml` lint config 变更。
- `ruff check src/ --select F841` → 0 errors。

## 后端逻辑
- N/A（lint 治理）。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-LINT-2 续（F841 0 errors） | `tests/unit/test_lint_baseline.py`：扩 `--select F401,F841` 断言 0（v1.4.0 仅 F401，本轮加 F841） |

## 实现就绪度
- [x] 27 errors 已定位（rff --statistics）
- [x] AC 覆盖 1/1
- 串行末位（所有 src 改动后），虚线依赖 I-1/I-4/Z-7
