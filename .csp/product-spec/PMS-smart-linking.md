---
type: module-spec
confidence: high
sources:
  - "[[docs/prd/PRD-smart-linking-v1.8.0.md]]"
  - "[[.csp/artifacts/retrospective-v1.7.0.md]]"
seeAlso:
  - "[[code-spec/saw/CODE-MODULE-SPEC.md]] §M09(query)"
created: "2026-09-04"
updated: "2026-09-04"
---

# PMS: smart-linking（智能链接 + AI 摘要）

> v1.8.0 新能力模块。roadmap v4.2 非 embedding 项：智能链接建议 + 链接审计 + AI 摘要。复用 query 引擎（related_pages/wiki_links/wiki_graph）+ LLMRouter，无新引擎。

## 模块边界
- **做什么**：
  - 智能链接建议（`saw links suggest`——相关未链接页建议）；
  - 链接审计（`saw links audit`——孤儿页 + 断链）；
  - AI 摘要（`saw summarize`——LLM 摘要 wiki 页）。
- **不做什么**：embedding 语义搜索（heavy SDK defer）；自动应用建议（只输出）；K1/K2/K3 债务。
- **PMS 边界=PRD §2 F-L-1..3**。复用 v1.6.0/v1.7.0 既有的 related_pages/wiki_links/wiki_graph/LLMRouter。

## 验收形态
- `saw links suggest <page>` 输出建议链接（slug + score + reason），已链接的不出现（AC-LINK-1）。
- `saw links audit` 输出孤儿页 + 断链（AC-LINK-2）。
- `saw summarize <page>` 在线产非空摘要；无 LLM 报错退出 1（AC-SUM-1）。

## 接口契约摘要（ground 自源码）
- related_pages：`engines/query/related_pages.py:compute_related_pages(slug, wiki_repo, top_k)`（3-signal 打分）。
- wiki_links：`engines/query/wiki_links.py:parse_wiki_links` + `extract_unique_targets`（outlinks 去重）。
- wiki_repo：`adapters/storage/wiki_repository.py:list_pages` + `read`。
- backlinks 逻辑：镜像 `drivers/web/routes/pages.py:get_backlinks`（扫描所有页的 outlinks 反建）。
- LLM：`adapters/llm/router.py:LLMRouter.answer_query(context, question, system_prompt)`。
- CLI 装配：复用 `query_cmd.py` 既有 wiki_repo 装配（load_config + WikiRepository）。

## 关联
- PRD: `docs/prd/PRD-smart-linking-v1.8.0.md`
- 上游复盘: `.csp/artifacts/retrospective-v1.7.0.md`（K1-K3 deferred 理由）
- 复用 PMS: `PMS-e2e-usability.md`（CLI 可用性）、`PMS-intelligence-adaptation.md`（LLM 在线路径）
- 下游 Spec: [待 03 回填] —— F-L-1..3 各 1 Spec
