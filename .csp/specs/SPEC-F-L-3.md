---
id: SPEC-F-L-3
title: AI 摘要（saw summarize）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-04"
prd_ref: docs/prd/PRD-smart-linking-v1.8.0.md
pms_ref: .csp/product-spec/PMS-smart-linking.md
feature_id: F-L-3
complexity: S
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-L-3]
---

# SPEC-F-L-3: summarize

## 实现 delta（ground 自源码）
- 新增 `drivers/cli/commands/summarize_cmd.py`（Typer command），`main.py` 注册。
- summarize：读 page content → `LLMRouter.answer_query(content, "Summarize this page", system_prompt)` → 打印摘要。
- 复用 `adapters/llm/router.py:LLMRouter.answer_query(context, question, system_prompt)` + query_cmd 既有 LLM 装配（load_config + detect_tier + LLMRouter）。
- 在线路径；无 LLM（tier < LIGHTWEIGHT）报错退出 1（不静默 fallback，PRD §4 风险）。

## 接口契约
- `saw summarize <page> [--path .]` → 在线产摘要（非空）；无 LLM 报错 exit 1。

## 后端逻辑
- read(slug) → LLMRouter.answer_query(page.content, summarize_prompt, system) → print。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-SUM-1（在线产非空摘要，无 LLM 报错） | `tests/unit/test_summarize_cmd.py`：mock LLMRouter.answer_query → 非空；无 LLM → exit 1 |

## 实现就绪度
- [x] LLMRouter.answer_query 就绪
- [x] AC 覆盖 1/1
