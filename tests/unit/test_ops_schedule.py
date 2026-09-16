"""Tests for D2 Write Queue status + A5 AgentScheduler (v1.27.0)."""
from __future__ import annotations

import sqlite3
from types import SimpleNamespace

import saw.drivers.mcp.tools.ops_tools as o
from saw.write_queue.queue import SQLiteWriteQueue, WriteOp


# ── D2 saw_queue_status ────────────────────────────────────────────

def _queue_with_ops(n_pending=0, n_done=0, n_dl=0):
    q = SQLiteWriteQueue(sqlite3.connect(":memory:"))
    for i in range(n_pending):
        q.enqueue([WriteOp(op_id=f"p{i}", session_id="s", sink_name="claims", payload={"content": f"p{i}"})])
    for i in range(n_done):
        op = WriteOp(op_id=f"d{i}", session_id="s", sink_name="claims", payload={})
        q.enqueue([op])
        q.mark_processing(op.op_id)
        q.mark_done(op.op_id)
    for i in range(n_dl):
        op = WriteOp(op_id=f"dl{i}", session_id="s", sink_name="claims", payload={})
        q.enqueue([op])
        q.mark_processing(op.op_id)
        for _ in range(5):
            q.mark_failed(op.op_id, "err")  # exhaust retries → dead_letter
    return q


def test_queue_status_empty():
    q = SQLiteWriteQueue(sqlite3.connect(":memory:"))
    s = q.status()
    assert s["total"] == 0
    assert s["pending"] == 0
    assert s["dead_letter"] == 0
    assert s["oldest_pending_age_s"] is None  # no pending


def test_queue_status_counts():
    q = _queue_with_ops(n_pending=3, n_done=2)
    s = q.status()
    assert s["pending"] == 3
    assert s["done"] == 2
    assert s["total"] == 5
    assert s["oldest_pending_age_s"] is not None  # has pending


def test_queue_status_dead_letter():
    q = _queue_with_ops(n_dl=1)
    s = q.status()
    assert s["dead_letter"] == 1


def test_saw_queue_status_tool(monkeypatch):
    """saw_queue_status MCP tool returns the queue status dict."""
    import asyncio
    q = _queue_with_ops(n_pending=1)
    monkeypatch.setattr(o, "_write_queue", q)
    res = asyncio.run(o.saw_queue_status())
    assert res["pending"] == 1


def test_saw_queue_status_no_queue(monkeypatch):
    import asyncio
    monkeypatch.setattr(o, "_write_queue", None)
    res = asyncio.run(o.saw_queue_status())
    assert res["error"] == "write_queue_not_initialized"


# ── A5 AgentScheduler (disabled path — no SAW_SCHEDULER_ENABLED=1) ─

def test_agent_scheduler_disabled_by_default():
    """Without SAW_SCHEDULER_ENABLED=1, schedule() is a no-op (disabled)."""
    import os
    assert os.environ.get("SAW_SCHEDULER_ENABLED", "0") == "0"  # default
    s = o.AgentScheduler()
    assert s.enabled is False
    ok = s.schedule("test", lambda: None, seconds=60)
    assert ok is False
    jobs = s.list_jobs()
    assert jobs[0]["status"] == "disabled"


def test_saw_schedule_tool_disabled(monkeypatch):
    """saw_schedule returns scheduled=False when the scheduler is disabled."""
    import asyncio
    s = o.AgentScheduler()  # disabled by default
    monkeypatch.setattr(o, "_scheduler", s)
    res = asyncio.run(o.saw_schedule(name="guardian_patrol", seconds=60))
    assert res["scheduled"] is False
