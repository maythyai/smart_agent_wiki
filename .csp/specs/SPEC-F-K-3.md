---
id: SPEC-F-K-3
title: coverage 推向 65（synthesize 测试 + ratchet 63→64）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-04"
prd_ref: docs/prd/PRD-graph-workspace-v1.7.0.md
pms_ref: .csp/product-spec/PMS-test-gate.md
feature_id: F-K-3
complexity: M
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-K-3]
---

# SPEC-F-K-3: synthesize 覆盖 + 棘轮

## 实现 delta（ground 自源码）
- v1.6.0 测得 synthesize/scheduler.py 32% / synthesize/engine.py 37%（retro J1）。
- 补 synthesize/engine.py（synthesize 流程）+ synthesize/scheduler.py（调度/优先级）单测，mock LLM/scheduler 确定性。
- coverage ratchet 63→64（实测达 64 设；65 仍 thin 若不达——硬约定 #10）。

## 接口契约
- `pyproject.toml: fail_under = 64`（实测达 64 后）。
- 新增 synthesize 测试文件。

## 后端逻辑
- N/A（测试治理）。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-COV-3（synthesize 覆盖 + ratchet 64） | `tests/unit/engines/synthesize/test_engine.py`/`test_scheduler.py`（新建）；`fail_under=64` |

## 实现就绪度
- [x] fail_under 机制就绪
- [x] AC 覆盖 1/1
- 串行 Wave 2
