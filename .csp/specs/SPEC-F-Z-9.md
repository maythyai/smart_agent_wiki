---
id: SPEC-F-Z-9
title: query 子模块测试 + coverage fail_under 60→65
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-03"
prd_ref: docs/prd/PRD-intelligence-adaptation-v1.5.0.md
pms_ref: .csp/product-spec/PMS-test-gate.md
feature_id: F-Z-9
complexity: M
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-Z-9]
---

# SPEC-F-Z-9: query 测试 + coverage 棘轮

## 实现 delta（ground 自源码）
- coverage `fail_under=60`（`pyproject.toml:124`），core-engine north-star 80%。query 子模块（`engines/query/`：compare/related_pages/tree_mode/graph_traverse/memory/cache）是覆盖率杠杆点（retro H5）。
- 本轮补 query 子模块单测（gap 由 `pytest --cov=src/saw/engines/query` 报告定位）。
- `fail_under` 60→65（棘轮上调，勿一步设 80 致 CI 恒红——硬约定 #10）。

## 接口契约
- `pyproject.toml: fail_under = 65`。
- `pytest --cov=src/saw/engines/query` 覆盖率提升（[TBD] 实测后回填具体 %）。

## 后端逻辑
- N/A（测试治理）。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-COV-1（query 覆盖提升 + 棘轮 65） | `tests/unit/engines/query/test_compare.py`/`test_related_pages.py`/`test_tree_mode.py`（新建/扩）：覆盖主分支 + 边界；`fail_under=65` CI 绿 |

## 实现就绪度
- [x] fail_under 机制就绪
- [x] AC 覆盖 1/1
- 子模块具体 gap 须 `--cov-report` 实测定位（05 实施时跑）
