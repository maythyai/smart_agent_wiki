---
id: SPEC-v1.35-context-api
project: smart-agent-wiki
version: 1.0
last_updated: 2026-11-06
status: approved
prd_ref: PRD-v1.35-structured-context-api
target_version: v1.35.0
---

# SPEC — v1.35.0 Structured Context API（轻量）

## F1+F3: `saw_context` MCP + REST

### MCP: `src/saw/drivers/mcp/tools/query.py` 新增 `saw_context`
```python
@mcp.tool
async def saw_context(query: str, mode: str = "hybrid",
                      confidence_min: str = "", freshness_min: int = 0,
                      limit: int = 10) -> dict:
    """v1.35.0 ★品类定位: unified structured context (vector+graph+state)."""
```
- mode: semantic|graph|drift|hybrid（drift=semantic+graph 简化合并，诚实标注）。
- dispatch: semantic → `_query_engine.query(query, mode="semantic", limit=limit)`；graph → `mode="graph"`；hybrid/drift → 两者合并。
- post-filter: claims 的 confidence < confidence_min → 排除，filtered_out 计数。
- bundle: `{mode, query, claims: [{uuid, content, confidence, source_uuid}], graph: {nodes, edges} | None, metadata: {total_claims, filtered_out, elapsed_ms, modes_used}, note}`。

### REST: `src/saw/api/routes/query_ingest_learn.py` 新增 `POST /api/v1/context`
- 同 MCP 逻辑（body: query, mode, confidence_min, freshness_min, limit）。
- 走 `request.app.state.query`。

## AC
- test_saw_context_semantic: mode=semantic → claims + metadata。
- test_saw_context_confidence_filter: confidence_min=cross_validated → 仅高置信 + filtered_out。
- test_saw_context_hybrid: mode=hybrid → claims+graph。
- REST test: POST /api/v1/context → 200 bundle。

## MCP 工具 39→40（expected_tools + README 同步）。