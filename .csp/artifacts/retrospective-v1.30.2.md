# 复盘 — v1.30.2 AUDIT-F-03 wiki 索引韧性（2026-09-18）

> 07 闭环校验。fix PATCH（单 fix）。前置：06-ship done（v1.30.2 tagged @6a7d4d3, pushed, Release 含 wheel+sdist）。

## 闭环校验：✅ 通过
| 链路 | 状态 | 证据 |
|---|---|---|
| PRD→Spec | ✅ | PRD-wiki-index-resilience-v1.30.2 Approved；SPEC-F-WIKI-INDEX-RESILIENCE 1:1 |
| Spec→Task | ✅ | wiki_indexer.py index_all per-page try/except + skip 计数 |
| AC→测试 | ✅ | test_index_all_skips_unparseable_page（坏页 raise + 好页正常 → 返回 1 不 raise）|
| commit→tag | ✅ | v1.30.2 @6a7d4d3 (release commit) |
| 测试/lint | ✅ | pytest 2400/0 fail；ruff 0；cov 68.43% |
| 构建+Release | ✅ | wheel+sdist；https://github.com/maythyai/smart_agent_wiki/releases/tag/v1.30.2 |

## 度量
- 1 fix done（AUDIT-F-03 closed）
- pytest 2400 passed（+1）
- coverage 68.43%（未回归）
- fix PATCH

## Findings（回流）
- 无新增 finding。
- 续留：AUDIT-F-01/04/05/06/08 + CRITIC-F-01 + E2E-BLOCKED-01（见 ARCHIVE-MANIFEST）。

## 教训
- AUDIT-F-03 暴露 indexing all-or-nothing 设计反模式——derived cache（FTS5）不应被单坏页阻断。同类审查应扩展到其它 "scan all" 路径（concept_graph 重建、adaptive_index）。
- v1.30.0 ship 时 `saw web` 启动日志有 warning 但未阻断（app.py:573 已 try/except log），实际是 index_all 返回 0（搜索不可用）——隐蔽失效。建议 06 前加 "index_all 返回 >0 或空库" 健康断言。

## 下游衔接 → v1.31.0
- v1.31.0 (feat MINOR)：Activity 持久化（AUDIT-F-05 deferred-gate 闭合）+ Provenance Verification API（saw_verify_provenance 增强 + /api/v1/provenance/{claim_id} REST + contamination scan）。
