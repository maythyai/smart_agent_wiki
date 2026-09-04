# Decomposition Delta — v1.8.0（2026-09-04）

> 新一轮 02 拆解 delta。源自 PRD-smart-linking-v1.8.0 + retrospective-v1.7.0.md（K1-K3 deferred）。
> smart-linking track：3 Feature（F-L-1..3），新能力，复用 query/LLM 引擎。

## 新增 Feature

| id | name | domain | priority | complexity | depends_on | wave | blocked_by | source | AC |
|---|---|---|---|---|---|---|---|---|---|
| F-L-1 | 智能链接建议（saw links suggest） | smart-linking | P0 | M | — | 1 | — | roadmap §v4.2 | AC-LINK-1 |
| F-L-2 | 链接审计（saw links audit: 孤儿页+断链） | smart-linking | P1 | M | — | 1 | — | roadmap §v4.2 | AC-LINK-2 |
| F-L-3 | AI 摘要（saw summarize） | smart-linking | P1 | S | — | 1 | — | roadmap §v4.2 | AC-SUM-1 |

## 原子 Feature → Spec 映射（03 1:1）
- F-L-1 → SPEC-F-L-1（links suggest）
- F-L-2 → SPEC-F-L-2（links audit）
- F-L-3 → SPEC-F-L-3（summarize）
> 3 原子 Feature = 3 Spec。

## DAG delta
- F-L-1 / F-L-2 / F-L-3 互相独立（F-L-1/L-2 同 links_cmd 文件 bundle；F-L-3 独立 summarize_cmd）。
- 无新环；无依赖。

## Wave 重排（v1.8.0）
- **Wave 1（并行）**：F-L-1 + F-L-2（同 links_cmd.py bundle）/ F-L-3（summarize_cmd.py）

## 共享资源串行
- links_cmd.py（F-L-1/L-2 bundle）：同文件 → 一 commit，不并行 split。
- wiki_repo 装配：复用 query_cmd 既有（load_config + WikiRepository），三 feature 共用 helper。

## NFR delta
- **可测性**：F-L-1/L-2 全离线确定性（real wiki_repo on tmp dir）；F-L-3 mock LLMRouter.answer_query。
- **性能**：F-L-2 反向链接扫描 O(pages²)——限 top N + 跳过 .saw/。
- **可用性**：CLI 复用既有 Rich table 输出 + 错误友好（query_cmd 模式）。

## 下游消费
- → 03：无 ADR（无 schema/架构变更）；3 Spec 1:1。
- → 04：~3 Task（L-1/L-2 bundle + L-3）；全 Wave 1。
