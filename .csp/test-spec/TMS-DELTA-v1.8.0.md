# TMS Delta — v1.8.0（2026-09-04）

> 03 测试规约 delta。smart-linking 新能力。增量用例。

## 新 AC 测试映射

| AC | Feature | 用例落点 | 状态 |
|---|---|---|---|
| AC-LINK-1（建议未链接页，已链接不出现） | F-L-1 | `tests/unit/test_links_cmd.py`（新建）：suggest：A 未链 B→建议 B；A 已链 C→C 不出现 | [TBD-impl] |
| AC-LINK-2（孤儿页 + 断链） | F-L-2 | 同上：A 无入链→孤儿；B [[missing]]→断链 | [TBD-impl] |
| AC-SUM-1（在线产非空摘要，无 LLM 报错） | F-L-3 | `tests/unit/test_summarize_cmd.py`（新建）：mock answer_query→非空；无 LLM→exit 1 | [TBD-impl] |

## 约定
- F-L-1/L-2 全离线确定性（real wiki_repo on tmp dir + CliRunner）。
- F-L-3 mock LLMRouter.answer_query（CI 无 LLM）。
- 无 ADR（无 schema/架构变更）。
