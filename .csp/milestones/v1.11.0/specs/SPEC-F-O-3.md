---
id: SPEC-F-O-3
title: workflow REST 统一读 DB（collaborate.py list_workflows 读 workflow_executions + merge live）
version: 1.0
status: Approved
author: lifecycle-orchestrator
date: "2026-09-05"
prd_ref: docs/prd/PRD-debt-closure-v1.11.0.md
pms_ref: .csp/product-spec/PMS-debt-closure.md
cms_ref: .csp/code-spec/saw/CODE-MODULE-SPEC.md
feature_id: F-O-3
complexity: M
tdd_ref: .csp/tech-design/TECH-DESIGN-SUMMARY.md
ac_coverage: 3/3
related_tasks: [.csp/tasks/TASKS-DELTA-v1.11.0.md#T-F-O-3]
---

# SPEC-F-O-3: workflow REST 统一读 DB

## 实现 delta（ground 自源码）

- **改动文件**：`src/saw/api/routes/collaborate.py` — `list_workflows` 函数（L328-335）。
- **现状**（ground）：`list_workflows`（L328-335）读 in-memory `_workflows` dict（L33 `_workflows: dict[str, dict[str, Any]] = {}`），按 `started_at` 排序取前 20。
- **目标**：改为读 `workflow_executions` DB 表（与 CLI `workflow_cmd.py::list_recent` L189-210 同源），merge live in-memory running workflow。
- **CLI 参照**：`src/saw/drivers/cli/commands/workflow_cmd.py::list_recent`（L189-210）读 `workflow_executions` 表，`ORDER BY COALESCE(updated_at, started_at) DESC LIMIT ?`。
- **DB 表**：`workflow_executions`（v4 migration 既有，列：`workflow_id` / `definition_name` / `status` / `steps_completed` / `steps_total` / `errors_json` / `updated_at` / `finished_at` / `started_at`）。

## 后端架构

### `list_workflows` 改动伪代码

```python
@router.get("/workflows")
async def list_workflows(
    request: Request,
    limit: int = Query(20, ge=1, le=100, description="Max runs to show"),
) -> dict[str, Any]:
    """List recent workflows (durable DB + live in-memory merge).

    Reads the persisted ``workflow_executions`` table (same source as CLI
    ``saw workflow list``), then merges any in-memory live running
    workflows that may not yet have a DB row or whose DB status is stale.
    """
    # 1. Read durable DB rows
    conn = getattr(request.app.state, "conn", None)
    if conn is None:
        # Fallback: no DB connection available → return in-memory only
        items = sorted(
            _workflows.values(),
            key=lambda w: w.get("started_at", ""),
            reverse=True,
        )
        return {"workflows": items[:limit], "total": len(items)}

    from saw.db.migrations import apply_migrations
    apply_migrations(conn)  # ensure workflow_executions table (v4)

    rows = conn.execute(
        "SELECT workflow_id, definition_name, status, steps_completed, "
        "steps_total, updated_at, finished_at "
        "FROM workflow_executions "
        "ORDER BY COALESCE(updated_at, started_at) DESC "
        "LIMIT ?",
        (limit,),
    ).fetchall()

    # 2. Build durable items from DB rows
    db_ids: set[str] = set()
    items: list[dict[str, Any]] = []
    for wid, name, st, sc, tot, updated, finished in rows:
        db_ids.add(wid)
        items.append({
            "workflow_id": wid,
            "definition_name": name,
            "status": st,
            "steps_completed": sc,
            "steps_total": tot,
            "updated_at": updated,
            "finished_at": finished,
        })

    # 3. Merge live in-memory running workflows not in DB (or stale status)
    for wid, wf in _workflows.items():
        if wid in db_ids:
            # Live overrides DB status if running (DB may be stale)
            if wf.get("status") == "running":
                for item in items:
                    if item["workflow_id"] == wid:
                        item["status"] = wf["status"]
                        item["steps_completed"] = wf.get("current_step", item["steps_completed"])
                        item["steps_total"] = wf.get("steps_total", item["steps_total"])
                        break
            continue
        # Live workflow not in DB (just started, not persisted yet)
        if wf.get("status") == "running":
            items.append({
                "workflow_id": wid,
                "definition_name": wf.get("workflow", "unknown"),
                "status": "running",
                "steps_completed": wf.get("current_step", 0),
                "steps_total": wf.get("steps_total", 0),
                "updated_at": wf.get("started_at"),
                "finished_at": None,
            })

    # 4. Sort merged by updated_at DESC, return top-N
    items.sort(key=lambda w: w.get("updated_at") or "", reverse=True)
    return {"workflows": items[:limit], "total": len(items)}
```

### merge 策略（HOW）

| 场景 | 处理 |
|---|---|
| DB 有记录 + in-memory 也有 + in-memory status=running | live 覆盖 DB status/steps（DB 可能 stale） |
| DB 有记录 + in-memory 无 | 用 DB 数据（durable 历史） |
| DB 无记录 + in-memory 有 + running | 追加 live run 到结果（刚启动未持久化） |
| DB 无记录 + in-memory 有 + completed/failed | 跳过（应已在 DB，可能并发竞争） |

### DB 查询

```sql
SELECT workflow_id, definition_name, status, steps_completed,
       steps_total, updated_at, finished_at
FROM workflow_executions
ORDER BY COALESCE(updated_at, started_at) DESC
LIMIT ?;
```

与 CLI `list_recent`（`workflow_cmd.py:197-203`）完全同源。

### 响应 schema（不变，向后兼容）

```json
{
  "workflows": [
    {
      "workflow_id": "uuid",
      "definition_name": "knowledge_review",
      "status": "completed|running|failed",
      "steps_completed": 4,
      "steps_total": 4,
      "updated_at": "2026-09-05T...",
      "finished_at": "2026-09-05T..."
    }
  ],
  "total": 5
}
```

> schema 不变（`{"workflows": [...], "total": N}`），仅数据源从 in-memory → DB + merge live。字段从 `_workflows` dict 的 `workflow`/`steps` 等 → DB 列 `definition_name`/`steps_completed`/`steps_total`，对齐 DB 列名（PRD §3.3 业务规则 3）。

### 异常处理

| 场景 | 处理 | 用户提示 |
|---|---|---|
| DB 无 `workflow_executions` 表（migration 未跑） | `apply_migrations(conn)` 确保 v4 表存在 | 无（自动 migration） |
| DB 查询失败（SQLite 异常） | catch + 返回 500 | `{"error": {"code": "DB_ERROR", "message": "..."}}` |
| `conn` 不可用（app.state.conn=None） | fallback 到 in-memory only（向后兼容） | 无 |

## API 契约

| Method | Path | 描述 | 认证 | 限流 |
|---|---|---|---|---|
| GET | `/api/v1/workflows` | List recent workflows (DB + merge live) | 既有 auth_dep | 既有 |

### 请求参数

| 参数 | 类型 | 默认 | 说明 |
|---|---|---|---|---|
| `limit` | int | 20 | Max runs to show (1-100) |

### 响应（2xx）

```json
{
  "workflows": [...],
  "total": 5
}
```

### 错误码

| Code | HTTP | 说明 |
|---|---|---|
| `DB_ERROR` | 500 | DB 查询失败 |

## 测试映射（AC→用例）

| AC | 用例落点 | 断言 |
|---|---|---|
| AC-WF-1（REST 读 DB） | `tests/unit/test_workflow_rest_db.py`（新建）：in-memory DB + apply_migrations + seed 3 workflow_executions → `GET /api/v1/workflows` → 返回 ≥3 条 + 字段含 workflow_id/status/steps | DB 读路径正确 |
| AC-WF-2（REST merge live） | `tests/unit/test_workflow_rest_db.py`（扩）：in-memory `_workflows` 有 1 running（DB 无记录）→ `GET /api/v1/workflows` → 返回含 live running | live merge 正确 |
| AC-WF-3（CLI/REST 语义一致） | `tests/unit/test_workflow_rest_db.py`（扩）：同 DB → CLI `list_recent` 逻辑 vs REST `list_workflows` → 同数据源（`workflow_executions` 表） | 结果集一致 |

## 安全考量

- REST 端点鉴权不变（既有 `auth_dep` 中间件，router 级）。
- DB 查询参数化（`LIMIT ?`），无注入风险。
- 返回不含 `errors_json`（敏感错误详情不暴露给 API 消费方）。

## 实现就绪度

- [x] 改动点明确（`collaborate.py:328-335 list_workflows`）
- [x] DB 查询与 CLI 同源（`workflow_cmd.py:197-203`）
- [x] merge 策略明确（live running 覆盖 DB stale / live not-in-DB 追加）
- [x] 响应 schema 不变（向后兼容）
- [x] 异常处理明确（无表 auto-migrate / conn=None fallback / 查询失败 500）
- [x] AC 覆盖 3/3
- [ ] REST 查询延迟 [TBD]（须 05 实施后与 CLI 同量级验证）
