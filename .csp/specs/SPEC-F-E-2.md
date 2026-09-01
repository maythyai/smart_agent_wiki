---
id: SPEC-F-E-2
title: 核心引擎覆盖率门禁（≥80%）
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-test-gate.md
cms_ref: "[无]"
feature_id: F-E-2
complexity: M
tdd_ref: .csp/tech-design/KEY-CHALLENGES.md
related_modules: []
ac_coverage: 2/2
---

# SPEC-F-E-2: 覆盖率门禁

## 实现 delta
- CI coverage 门禁：核心引擎 ≥80%、非核心 ≥60%；未达 → CI 红 + 指未达模块+实际值。
- 分阶段提至 80%（基线低时）。

## 后端逻辑
- coverage 阈值配置 + fail-under；未达模块定位报告。

## 测试映射
| AC | 用例 |
|---|---|
| AC-TEST-1（核心 ≥80% 否则红） | `test_coverage_gate_core` |
| 未达模块指明 | `test_coverage_gate_reports_module` |

## 实现就绪度
- [x] AC 覆盖 2/2；依赖 F-E-1 基线
