---
id: PRD-smart-linking-v1.8.0
title: Smart Linking + AI Summarization
version: 1.0
status: Released
author: lifecycle-orchestrator
date: "2026-09-04"
product_type: platform
feature_count: 3
mvp_scope: [smart-linking-suggest, link-audit, ai-summarize]
thin_sections: [3]
upstream_source: "docs/strategy/ROADMAP.md#v4.2 + .csp/artifacts/retrospective-v1.7.0.md (findings K1-K3 deferred)"
target_version: v1.8.0
roadmap_ref: ROADMAP
related_pms:
  - .csp/product-spec/PMS-e2e-usability.md
  - .csp/product-spec/PMS-intelligence-adaptation.md
related_decomposition: .csp/decomposition/DECOMPOSITION-SUMMARY.md
related_retrospective: .csp/artifacts/retrospective-v1.7.0.md
---

# PRD-smart-linking-v1.8.0：Smart Linking + AI Summarization

> v1.7.0 闭环后的新一轮 01。**转新能力**：v1.7.0 retro 明确"workspace 故事告一段落，下一轮可转新能力"。本轮开 roadmap v4.2 的两项非 embedding 能力——智能链接 + AI 摘要——复用现已成熟的 query/compile 引擎，无新引擎。

## 1. 背景与动机（roadmap v4.2 + 复盘 K1-K3 决策）

v1.5.0–v1.7.0 三轮债务收口（workspace 三闭环 + coverage + scope 清理）告一段落。retrospective-v1.7.0.md findings K1-K3 经 review **本轮均不采纳**，理由：
- **K1（coverage 65 / compile/compiler 17%）defer**：复杂编译器深覆盖低 ROI；3 轮债务已够；retro 自身建议转新能力。fail_under 持 64，K1 续留 finding。
- **K2（per-request workspace 注入）defer**：local-first 单机工具，多 workspace 请求级注入非近期生产需求；隔离在引擎层已闭环，请求级 scope 是镀金直到多租户为真。
- **K3（entity_relation 冗余列）defer**：纯性能，无观测问题。
本轮开新能力，对齐 roadmap v4.2（Semantic Features 的非 embedding 项）。

## 2. 范围（3 Feature 组）

### F-L-1：智能链接建议（`saw links suggest <page>`）
对给定 wiki 页，找出**相关但尚未 `[[链接]]` 的页面**并建议。复用 `compute_related_pages`（3-signal 打分：shared tags/links/type affinity）+ `extract_unique_targets`（排除已有 outlinks）。CLI surface，全离线（确定性）。
- **AC-LINK-1**：`saw links suggest <page>` 输出建议链接列表（slug + score + reason），已链接的不出现。

### F-L-2：链接审计（`saw links audit`）
知识库维护：**孤儿页**（无反向链接的页面）+ **断链**（`[[target]]` 指向不存在的页）。复用 `list_pages` + `parse_wiki_links` + 反向链接扫描（镜像 web `/backlinks` 逻辑）。CLI surface，全离线。
- **AC-LINK-2**：`saw links audit` 输出孤儿页 + 断链列表（exit 0 有/无均报告）。

### F-L-3：AI 摘要（`saw summarize <page>`）
对 wiki 页内容做 AI 摘要。复用 `LLMRouter.answer_query`（context=page content, question="summarize"）。在线路径；CI 无 LLM 时报错退出（不静默 fallback），测试 mock。
- **AC-SUM-1**：`saw summarize <page>` 在线产摘要（非空）；无 LLM 报错退出 1。

## 3. 非目标
- embedding-based 语义搜索（需 sentence-transformers heavy SDK，v1.3.0 Z-5 已 defer，本轮仍 defer）。
- 链接的自动应用（建议只输出，不自动改文件——用户审阅后手改）。
- K1/K2/K3 债务（本轮不开，见 §1 理由）。

## 4. 风险
- **F-L-1 相关度**：`compute_related_pages` 是启发式（shared tags/links/type），建议可能噪声——top_k 限制 + reason 透明。
- **F-L-3 在线**：需 LLM；CI 无 LLM → mock；离线不 fallback（PRD 风险同 v1.5.0 distill）。
- **F-L-2 反向链接扫描成本**：O(pages²) 扫描；大库须限（top N + 跳过 .saw/）。

## 5. 下游衔接
- → 02 拆解：F-L-1..3 各拆 Feature + DAG；F-L-1/L-2 共享 links 域（同 CLI 文件）。
- → 03：无 ADR（无 schema/架构变更）；3 Spec 1:1。
- → 04：~3-4 Task；F-L-1/L-2 bundle（同 links_cmd）；F-L-3 独立。
