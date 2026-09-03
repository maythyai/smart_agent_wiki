---
id: SPEC-F-J-3
title: query 深覆盖（engine/compare/tree_mode → 65%）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-03"
prd_ref: docs/prd/PRD-debt-closure-v1.6.0.md
pms_ref: .csp/product-spec/PMS-test-gate.md
feature_id: F-J-3
complexity: M
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-J-3]
---

# SPEC-F-J-3: query 深覆盖 + 棘轮 63→65

## 实现 delta（ground 自源码）
- v1.5.0 测得 query 子模块：engine.py 14% / compare.py 23% / tree_mode.py 21%（杠杆点，retro I2）。
- 补 `engines/query/engine.py`（query mode 分发 / _graph_query / _compare_query / _tree_query / _parse_layered_answer / _extract_citations）+ `compare.py`（compare）+ `tree_mode.py`（search / _build_section_paths）单测。
- coverage fail_under 63→65（棘轮上调，硬约定 #10：须实测达 65 再设）。

## 接口契约
- `pyproject.toml: fail_under = 65`（实测达 65 后）。
- 新增 query 子模块测试文件。

## 后端逻辑
- N/A（测试治理）。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-COV-2（query 覆盖→65） | `tests/unit/engines/query/test_engine_modes.py`（新建：query 分发+各 mode）/ `test_compare.py`（扩）/ `test_tree_mode.py`（扩）；`fail_under=65` |

## 实现就绪度
- [x] fail_under 机制就绪
- [x] AC 覆盖 1/1
- 串行 Wave 2（J-1 代码落定后测 tree_mode）
