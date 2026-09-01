---
id: SPEC-F-A-3
title: query 链路冒烟（关键词+NL）
version: 1.0
status: Draft
author: "[TBD]"
date: "2026-09-01"
prd_ref: docs/prd/PRD-product-hardening-v1.md
pms_ref: .csp/product-spec/PMS-e2e-usability.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-A-3
complexity: M
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
related_modules: [SHARED-SCHEMAS.md]
ac_coverage: 2/2
---

# SPEC-F-A-3: query 冒烟

## 实现 delta（源自 CMS §M02）
- 冒烟节点：关键词 query + NL query，断言返回带 citation 且可溯源。
- 复用 `QueryEngine.query`（`engines/query/engine.py:82`）、`_keyword_search`（:194）、`_nl_query`（:124）、`FTS5Search`、`ContextCompiler`。
- NL 在线用 `LLMRouter`；离线由 F-A-5 走规则 fallback。

## 接口契约
- 冒烟节点（被 F-A-1 调用）。既有 `POST /api/v1/query`（`api/routes/query_ingest_learn.py:66`）可作集成冒烟入口。

## 后端逻辑
- query(keyword) → FTS5Search → 断言结果带 citation。
- query(NL) → _nl_query → LLMRouter → 断言答案带引用。

## 性能 NFR
- query 关键词 P99 < 500ms（冒烟内置性能断言）。

## 测试映射
| AC | 用例 |
|---|---|
| 关键词 query 带 citation 可溯源 | `test_smoke_query_keyword_citation` |
| NL query 走 _nl_query 带引用 | `test_smoke_query_nl_citation` |

## 实现就绪度
- [x] AC 覆盖 2/2；NL 在线/离线分流由 F-A-5
