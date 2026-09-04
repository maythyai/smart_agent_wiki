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

## v1.5.0 delta（2026-09-03）
| 层 | v1.5.0 增量 | 校验 |
|---|---|---|
| PRD feature_count | 4 新能力 + 4 债 | PRD-intelligence-adaptation-v1.5.0 §2 ✓ |
| decomposition 原子 Feature | +8（F-I-1..4 + F-Z-6..9） | DECOMPOSITION-DELTA-v1.5.0 ✓ |
| Spec | +8（SPEC-F-I-1..4 + SPEC-F-Z-6..9） | 强校验 == Feature 数 ✓（1:1） |
| ADR | +2（ADR-006 resume / ADR-007 workspace scope） | 驱动 F-I-1 / F-Z-7 ✓ |
| TMS | +10 用例（TMS-DELTA-v1.5.0） | AC 10/10 ✓ |
| PRD AC（v1.5.0） | 10（AC-WF-1/2, AC-LR-1/2, AC-TK-1, AC-AG-1, AC-LINT-2续, AC-WS-3, AC-SEC-5续, AC-COV-1） | 10/10 ✓ |

## v1.6.0 delta（2026-09-03）
| 层 | v1.6.0 增量 | 校验 |
|---|---|---|
| PRD feature_count | 4 债务收口 | PRD-debt-closure-v1.6.0 §2 ✓ |
| decomposition 原子 Feature | +4（F-J-1..4） | DECOMPOSITION-DELTA-v1.6.0 ✓ |
| Spec | +4（SPEC-F-J-1..4） | 强校验 == Feature 数 ✓（1:1） |
| ADR | +1（ADR-008 workspace 写入策略） | 驱动 F-J-2 ✓ |
| TMS | +4 用例（TMS-DELTA-v1.6.0） | AC 4/4 ✓ |
| PRD AC（v1.6.0） | 4（AC-WS-4, AC-WS-5, AC-COV-2, AC-SEC-6） | 4/4 ✓ |

## v1.7.0 delta（2026-09-04）
| 层 | v1.7.0 增量 | 校验 |
|---|---|---|
| PRD feature_count | 3 债务收口 III | PRD-graph-workspace-v1.7.0 §2 ✓ |
| decomposition 原子 Feature | +3（F-K-1..3） | DECOMPOSITION-DELTA-v1.7.0 ✓ |
| Spec | +3（SPEC-F-K-1..3） | 强校验 == Feature 数 ✓（1:1） |
| ADR | +1（ADR-009 entity workspace 隔离） | 驱动 F-K-1 ✓ |
| TMS | +3 用例（TMS-DELTA-v1.7.0） | AC 3/3 ✓ |
| PRD AC（v1.7.0） | 3（AC-WS-6, AC-ARCH-1, AC-COV-3） | 3/3 ✓ |

## v1.8.0 delta（2026-09-04）
| 层 | v1.8.0 增量 | 校验 |
|---|---|---|
| PRD feature_count | 3 新能力（smart linking + summarize） | PRD-smart-linking-v1.8.0 §2 ✓ |
| decomposition 原子 Feature | +3（F-L-1..3） | DECOMPOSITION-DELTA-v1.8.0 ✓ |
| Spec | +3（SPEC-F-L-1..3） | 强校验 == Feature 数 ✓（1:1） |
| ADR | — | 无架构变更（新能力复用引擎） |
| TMS | +3 用例（TMS-DELTA-v1.8.0） | AC 3/3 ✓ |
| PRD AC（v1.8.0） | 3（AC-LINK-1, AC-LINK-2, AC-SUM-1） | 3/3 ✓ |

## v1.9.0 delta（2026-09-04)
| 层 | v1.9.0 增量 | 校验 |
|---|---|---|
| PRD feature_count | 3 新能力（agent/workflow 可见性） | PRD-agent-viz-v1.9.0 §2 ✓ |
| decomposition 原子 Feature | +3（F-M-1..3） | DECOMPOSITION-DELTA-v1.9.0 ✓ |
| Spec | +3（SPEC-F-M-1..3） | 强校验 == Feature 数 ✓（1:1） |
| ADR | — | 无架构变更（复用基建） |
| TMS | +3 用例（TMS-DELTA-v1.9.0） | AC 3/3 ✓ |
| PRD AC（v1.9.0） | 3（AC-WF-3, AC-AG-2, AC-API-1） | 3/3 ✓ |

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
