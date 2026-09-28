---
id: SPEC-F-CONTAMINATION-SCAN
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-18
status: approved
prd_ref: PRD-contamination-scan-v1.31.1
target_version: v1.31.1
---

# SPEC — contamination scan（v1.31.1）

## 逻辑
1. 查已解决 SUPERSEDED 矛盾：
   `SELECT uuid, claim_a_uuid, claim_b_uuid FROM contradictions WHERE resolution='superseded' AND resolved_at IS NOT NULL`
   → `superseded_sources` = set(claim_a_uuid ∪ claim_b_uuid)，并记 mapping {source_uuid: [contradiction_uuid,...]}。
2. 找衍生 claim（source 指向 superseded 源，且自身非源）：
   `SELECT uuid, content, source_uuid FROM claim WHERE source_uuid IN (...) AND deleted_at IS NULL AND uuid NOT IN (...)`
   → contaminated claims。
3. 返回：`[{claim_uuid, content(trunc 200), source_uuid, contradiction_ids:[...], reason:"superseded_source"}]`。

## F-CS-1: `saw_contamination_scan` MCP
`src/saw/drivers/mcp/tools/govern.py` 新增：
```python
@mcp.tool
async def saw_contamination_scan() -> dict:
    """v1.31.1: scan for claims derived from superseded sources (knowledge contamination)."""
    # uses _governor.claims_repo._conn
    # returns {contaminated: [...], count, scanned}
```

## F-CS-2: `GET /api/v1/contamination` REST
`src/saw/api/routes/govern.py` 新增 `@router.get("/contamination")`，同逻辑，依赖 `_claims_repo`。

## AC
- 无 SUPERSEDED 矛盾 → `{"contaminated": [], "count": 0}`。
- 构造矛盾（claim_a vs claim_b, resolution=superseded, resolved_at set）+ 衍生 claim（source_uuid=claim_a）→ scan 返回该衍生 claim，reason=superseded_source，不含 claim_a/b 自身。
- MCP + REST 一致。

## 测试
- `tests/unit/drivers/test_mcp_tools.py` 或 `tests/unit/engines/govern/test_contamination.py`：构造 superseded 矛盾 + 衍生 claim → scan 命中。
- `tests/api/test_h1_routes.py::TestContaminationRoute`：REST 空列表 + 命中。
- 全量回归 + ruff 0 + coverage 不回归。
