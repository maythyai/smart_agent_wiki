---
id: SPEC-F-L-1
title: 智能链接建议（saw links suggest）
version: 1.0
status: Draft
author: lifecycle-orchestrator
date: "2026-09-04"
prd_ref: docs/prd/PRD-smart-linking-v1.8.0.md
pms_ref: .csp/product-spec/PMS-smart-linking.md
feature_id: F-L-1
complexity: M
ac_coverage: 1/1
related_tasks: [.csp/tasks/WBS.md#T-F-L-1]
---

# SPEC-F-L-1: links suggest

## 实现 delta（ground 自源码）
- 新增 `drivers/cli/commands/links_cmd.py`（Typer sub-app：suggest + audit），`main.py` 注册 `app.add_typer(links_app, name="links")`。
- suggest：读 page content → `extract_unique_targets(content)` 得已有 outlinks → `compute_related_pages(slug, wiki_repo, top_k)` 得相关页 → 过滤掉已链接的 + 自身 → 输出（slug + score + reason）。
- 复用 `engines/query/related_pages.py:compute_related_pages`（3-signal 打分）+ `engines/query/wiki_links.py:extract_unique_targets`。**不改引擎**。
- wiki_repo 装配复用 query_cmd（load_config + WikiRepository(wiki_path/"wiki")）。

## 接口契约
- `saw links suggest <page> [--path .]` → 输出建议表（slug/score/reason）；exit 0。
- 已 `[[链接]]` 的页不出现；无建议时打印 "no suggestions"。

## 后端逻辑
- read(slug) → outlinks = extract_unique_targets(content) → related = compute_related_pages(slug, wiki_repo) → filter(outlinks ∪ {slug}) → print top_k。

## 测试映射（AC→用例）
| AC | 用例 |
|---|---|
| AC-LINK-1（建议未链接页，已链接不出现） | `tests/unit/test_links_cmd.py`：两页共享 tag，page A 未链 B → 建议 B；A 已链 C → C 不出现 |

## 实现就绪度
- [x] compute_related_pages + extract_unique_targets 全就绪
- [x] AC 覆盖 1/1
