---
id: SPEC-F-PROVENANCE-ACTIVITY
project: smart-agent-wiki
version: 1.0
last_updated: 2026-09-18
status: approved
prd_ref: PRD-provenance-activity-v1.31.0
target_version: v1.31.0
---

# SPEC — v1.31.0 Provenance API + Activity 持久化（详细）

## F-PA-1: Activity 持久化（AUDIT-F-05 闭合）

### 1.1 v12 migration — `agent_activity` 表
`src/saw/db/migrations.py` 追加：
```python
def _create_agent_activity(conn):
    conn.executescript("""CREATE TABLE IF NOT EXISTS agent_activity (
    agent_name TEXT PRIMARY KEY,
    calls INTEGER NOT NULL DEFAULT 0,
    failures INTEGER NOT NULL DEFAULT 0,
    last_action TEXT,
    last_active_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_agent_activity_active ON agent_activity(last_active_at);""")
_register(12, _create_agent_activity)
```

### 1.2 `AgentActivityTracker` 持久化
`src/saw/engines/collaborate/activity_tracker.py`：
- `__init__(self, conn=None)`：存 `self._conn`。
- `attach_conn(conn)`：设 `self._conn` + `self.load()`。
- `load()`：`SELECT * FROM agent_activity` → 重建 `self._activities` dict（重启恢复）。
- `_handle_event`：内存更新后，若 `self._conn` → `upsert` 到 `agent_activity`（agent_name, calls, failures, last_action, last_active_at, updated_at）。try/except 不阻塞 event。
- `get_activity`/`get_summary`：不变（读内存）。

### 1.3 lifespan 接线
`src/saw/drivers/web/app.py` lifespan：activity tracker init 后，在 wq/conn 可用块内调 `_activity_tracker_inst.attach_conn(_db_conn)`（_db_conn = `_wq._conn`）。仅 web 模式（CLI 模式 conn=None，degrade 内存态，不阻塞）。

### AC
- 单测：tracker(conn) → 模拟 2 个 WorkflowStep event → 新 tracker(conn) load → get_activity 一致（calls=2）。
- 跨重启不丢。

## F-PA-2: `GET /api/v1/provenance/{claim_id}` REST

`src/saw/api/routes/govern.py` 新增：
```python
@router.get("/provenance/{claim_id}")
def get_provenance(claim_id, repo=Depends(_claims_repo)):
    # trace chain by following source_uuid up to root (source_uuid == uuid or not found)
    # cap depth 10 (cycle guard)
    # each node: {uuid, content (truncated 200), source_uuid, page_location, confidence, receipt_id?}
    # receipt_id: SELECT receipt_id FROM receipts WHERE claim_uuid=? LIMIT 1
```
- 链构建：start=claim_id; while node := repo.get_by_id(cur) and cur != node.source_uuid and depth<10: append node; cur = node.source_uuid. 末节点为根源（page_number/line_number 即原文位置）。
- 404 if start claim not found.

### AC
- `GET /api/v1/provenance/{uuid}` 200 返回 `{claim_id, chain:[...], depth, root_source:{page_location,...}}`。
- claim 不存在 → 404。
- 环/自引用 → depth cap 10，不无限循环。

## F-PA-3: `saw_verify` MCP 增强
`src/saw/drivers/mcp/tools/govern.py saw_verify`：result.provenance 增：
- `source_claim_uuid`: chain.source_uuid（已有，重命名暴露）。
- `receipt_id`: 从 receipts 表查（`SELECT receipt_id FROM receipts WHERE claim_uuid=? LIMIT 1`），经 `_governor.claims_repo._conn`；None if 无 receipt。

### AC
- `saw_verify(uuid)` output 含 `source_claim_uuid` + `receipt_id`（或 null）。

## 测试
- `tests/unit/engines/collaborate/test_activity_tracker_persistence.py`：persist + load 一致。
- `tests/unit/api/routes/test_govern_provenance.py`：REST chain + 404 + cycle cap。
- `tests/unit/drivers/test_mcp_tools.py`：saw_verify output 含新字段（扩展既有 test）。
- 全量回归 + ruff 0 + coverage 不回归。

## contamination scan（deferred → v1.31.1）
本版不含。v1.31.1 01 入口清单含此项 + 解除条件（v1.31.0 released）。
