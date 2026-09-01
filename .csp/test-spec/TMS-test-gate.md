# TMS: test-gate — 测试说明书

> 继承 PMS-test-gate。Feature：F-E-1..3。

## 需求→方法追溯矩阵
| AC | Feature | 用例 | 类型 | 断言 |
|---|---|---|---|---|
| AC-TEST-1 | F-E-2 | test_coverage_gate_core / test_coverage_gate_reports_module | CI | 核心 ≥80% 否则红 |
| AC-TEST-2 | F-E-3 | test_ci_integrated_runs / test_coverage_report_trend | CI | CI 单测+冒烟+coverage 全跑 |
| (基线) | F-E-1 | test_coverage_baseline_measured / test_threshold_set | CI | 基线实测+阈值设定 |

## 入口×状态增量矩阵
| 入口 | 达标 | 未达 | 冒烟失败 |
|---|---|---|---|
| CI test job | ✓ 绿 | ✓ 红+模块 | — |
| CI smoke job | ✓ 绿 | — | ✓ 红 |

## 存量用例
- F-E-1: 2 / F-E-2: 2 / F-E-3: 2 = 6 用例

## 缺口
- [TBD] 覆盖率基线数值首次实测后定；阈值分阶段提。
