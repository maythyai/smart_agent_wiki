# Traceability Summary — 追溯汇总

> PRD ↔ Feature ↔ Spec ↔ TMS ↔ AC 双向追溯。粒度：PRD 模块 → decomposition 域 → 原子 Feature → Spec（1:1）。

## 数量一致性
| 层 | 数量 | 校验 |
|---|---|---|
| PRD feature_count（模块） | 5 | 弱校验 ≈ 域数 ✓ |
| decomposition 域 | 5 | = PMS 模块 ✓ |
| decomposition 原子 Feature | 20 | — |
| Spec | 20 | 强校验 == Feature 数 ✓（1:1） |
| TMS 模块 | 5 | = PMS 模块 ✓ |
| PRD AC | 11 | 已覆盖 11/11 ✓ |

## 追溯链
- 正向：`FORWARD-MATRIX.md`（PRD→Feature→Spec）
- 反向：`BACKWARD-MATRIX.md`（Spec→Feature→PRD）
- 覆盖：`COVERAGE-REPORT.md`（AC 11/11，缺口 0）

## 回填状态
- PRD front-matter `related_specs`：20 Spec 路径待回填（本 commit 完成）
- PRD `related_decomposition`：已回填（02 阶段）
- manifest：spec/tms/adr items 待回写（本 commit 完成）

## [TBD] 留尾（实现期待验，非追溯缺口）
receipt 覆盖率 / 前端 token 互通 / 覆盖率基线 / 冒烟命令名。
