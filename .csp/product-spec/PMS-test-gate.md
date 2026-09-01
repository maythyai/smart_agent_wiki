---
type: module-spec
confidence: high
sources:
  - "[[docs/prd/PRD-product-hardening-v1.md]]"
seeAlso:
  - "[[product-spec/PMS-e2e-usability]]"
created: "2026-09-01"
updated: "2026-09-01"
---

# PMS: test-gate（测试覆盖门禁）

## 模块边界
- **做什么**：为 engines/{ingest,query,govern,collaborate,compile} + write_queue 核心路径建立覆盖率门禁与回归基线；CI 不达门禁阻断合并；冒烟（e2e-usability）随 CI 跑且全过。
- **不做什么**：不定义测试框架选型（HOW）；非核心模块覆盖率 [TBD] 阈值归 V1.1；不重写既有 128 个测试。
- **PMS 边界=PRD §3.5**。

## 验收形态
- CI 跑单测 + 冒烟 + coverage，核心引擎链路 ≥80%（基线 [TBD] 首次实测后定），非核心 ≥60%。
- 门禁失败 → CI 红 + 指未达模块。
- 覆盖率报告入产物，趋势可查。

## 接口契约摘要
- CI：`.github/workflows/ci.yml`。
- 覆盖率：`pytest --cov` 报告（实现细节 HOW）。
- 冒烟依赖：`PMS-e2e-usability` 的冒烟命令。

## 关联
- PRD: `docs/prd/PRD-product-hardening-v1.md` §3.5
- 依赖 PMS: `PMS-e2e-usability`（冒烟基线）
- 现状：128 `test_*.py`，覆盖率 [TBD]
- 下游 Spec: [待 03 回填]
