# 复盘 — v1.35.0 Structured Context API v1（2026-11-07）

> 07 闭环。feat MINOR ★品类定位。前置 06-ship done。

| 链路 | 状态 |
|---|---|
| 四读+收敛闸门→PRD engineering | ✅ convergence 通过 + PRD-v1.35 upgrade (engineering Approved) |
| Spec→Task | ✅ saw_context MCP (query.py) + POST /api/v1/context REST + 40 tools |
| S6 动态门控 | ✅ pytest 2441/0, cov 68.51% (gate 68), ruff 0, tsc clean |
| 双闸门 | ✅ vi=0 fc=0 |
| push+Release | ✅ v1.35.0 @3c24e08c, wheel+sdist |

## 度量
- 3 feat (F1+F3+F5 partial): saw_context 统一 API + state filters + REST
- MCP 39→40
- pytest 2441 (+4)

## Lessons
- 版本 bump 用 raw string replace 不用 regex（regex `\.35` 会引入转义污染 `1\.35\.0`——v1.35.0 曾踩，已修）
- semantic search 依赖 FTS 索引——测试须 seed fts_index entry（只 insert claim 表不够）
- drift mode v1 = 简化 hybrid（诚实标注 note，不假装完整 community primer）

## 下游 → v1.36.0
- v1.36.0 (intelligence): Incremental Graph + Logical-Symbolic Reasoning + Deep Research v2（v1.36+v1.45 合并）。
- PRD SPEC planning Draft 已有（docs/prd/PRD-v1.36-incremental-graph-reasoning.md）→ 01 升级 engineering。