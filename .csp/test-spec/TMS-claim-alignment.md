# TMS: claim-alignment — 测试说明书

> 继承 PMS-claim-alignment。Feature：F-B-1..3。

## 需求→方法追溯矩阵
| AC | Feature | 用例 | 类型 | 断言 |
|---|---|---|---|---|
| AC-ALIGN-1 | F-B-1 | test_claim_diff_mcp / test_claim_diff_clean | 单元 | 宣称与代码 0 diff |
| AC-ALIGN-2 | F-B-2 | test_capabilities_has_file_line / test_capabilities_unverified_marked | 单元 | file:line + [unverified] |
| (历史标注) | F-B-3 | test_doc_aligned_or_marked / test_deep_audit_historical_marker | 单元 | 一致或加历史快照 |

## 入口×状态增量矩阵
| 入口 | 有 diff | 0 diff | unverified |
|---|---|---|---|
| claim_diff.sh | ✓ 报告 | ✓ 退出0 | — |
| gen_capabilities.sh | — | — | ✓ 标记 |

## 存量用例
- F-B-1: 2 / F-B-2: 2 / F-B-3: 2 = 6 用例

## 缺口
- 无。
