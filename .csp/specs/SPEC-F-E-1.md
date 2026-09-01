---
id: SPEC-F-E-1
title: 覆盖率基线实测 + 阈值设定
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-test-gate.md
cms_ref: "[无]"
feature_id: F-E-1
complexity: M
tdd_ref: .csp/tech-design/KEY-CHALLENGES.md
related_modules: []
ac_coverage: 2/2
---

# SPEC-F-E-1: 覆盖率基线

## 实现 delta
- `pytest --cov=src/saw` 实测现有 128 测试覆盖率 → 基线数值 [TBD]。
- 定阈值：核心引擎（ingest/query/govern/collaborate/compile + write_queue）≥80%；非核心 ≥60%。

## 后端逻辑
- coverage 报告产物 + 基线记录（`.csp/artifacts/coverage-baseline.md` [TBD]）。

## 测试映射
| AC | 用例 |
|---|---|
| 现有 128 测试产基线 | `test_coverage_baseline_measured` |
| 阈值核心≥80%/非核心≥60% | `test_threshold_set` |

## 实现就绪度
- [x] AC 覆盖 2/2
- [TBD] 基线数值首次实测后定
