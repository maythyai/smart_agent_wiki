"""Tests for the agent-native MCP tools saw_resolve / saw_record (C1/C2, v1.22.0)."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

import saw.drivers.mcp.tools.agent_tools as at


def _set_globals(**kw):
    """Patch agent_tools globals and restore after the test."""
    saved = {k: getattr(at, k) for k in ("_query_engine", "_code_graph_engine", "_write_queue")}
    for k, v in kw.items():
        setattr(at, k, v)

    def restore():
        for k, v in saved.items():
            setattr(at, k, v)
    return restore


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


# ── C1 saw_resolve ─────────────────────────────────────────────────

def test_saw_resolve_aggregates_claims_with_confidence():
    """saw_resolve returns claims with confidence + score from the search."""
    claim = SimpleNamespace(
        uuid="c1", content="rate limit login", confidence=SimpleNamespace(name="VERIFIED"),
        freshness=SimpleNamespace(value=2),
    )
    claims_repo = SimpleNamespace(get_by_id=lambda uid: claim if uid == "c1" else None)
    search = SimpleNamespace(search=lambda q, limit=10: SimpleNamespace(
        claim_uuids=["c1"], contents=["rate limit login"], scores=[0.9],
    ))
    qe = SimpleNamespace(_claims_repo=claims_repo, _search=search)
    restore = _set_globals(_query_engine=qe, _code_graph_engine=None)
    try:
        res = _run(at.saw_resolve(task="add rate limit to login", limit=5))
    finally:
        restore()
    assert res["task"] == "add rate limit to login"
    assert len(res["claims"]) == 1
    assert res["claims"][0]["uuid"] == "c1"
    assert res["claims"][0]["confidence"] == "verified"
    assert res["claims"][0]["score"] == 0.9
    assert res["freshness_warning"] is None  # freshness 2 < 6


def test_saw_resolve_flags_stale_claims():
    """Aging claims (freshness >= 6) are surfaced in freshness_warning."""
    claim = SimpleNamespace(
        uuid="c-stale", content="old claim", confidence=SimpleNamespace(name="UNVERIFIED"),
        freshness=SimpleNamespace(value=7),
    )
    claims_repo = SimpleNamespace(get_by_id=lambda uid: claim)
    search = SimpleNamespace(search=lambda q, limit=8: SimpleNamespace(
        claim_uuids=["c-stale"], contents=["old"], scores=[0.5],
    ))
    qe = SimpleNamespace(_claims_repo=claims_repo, _search=search)
    restore = _set_globals(_query_engine=qe, _code_graph_engine=None)
    try:
        res = _run(at.saw_resolve(task="x"))
    finally:
        restore()
    assert res["freshness_warning"] == ["c-stale"]


def test_saw_resolve_no_query_engine():
    """Without a query engine, saw_resolve returns a clear error."""
    restore = _set_globals(_query_engine=None, _code_graph_engine=None)
    try:
        res = _run(at.saw_resolve(task="x"))
    finally:
        restore()
    assert res["error"] == "query_engine_not_initialized"


# ── C2 saw_record ───────────────────────────────────────────────────

def test_saw_record_enqueues_claim_writeop():
    """saw_record enqueues a WriteOp to the claims sink with the decision payload."""
    enqueued = []

    class _WQ:
        def enqueue(self, ops):
            enqueued.extend(ops)

    restore = _set_globals(_query_engine=None, _code_graph_engine=None, _write_queue=_WQ())
    try:
        res = _run(at.saw_record(summary="Use Argon2 for password hashing", kind="decision", confidence="verified"))
    finally:
        restore()
    assert res["recorded"] is True
    assert res["kind"] == "decision"
    assert res["confidence"] == "verified"
    assert res["summary"] == "Use Argon2 for password hashing"
    assert len(enqueued) == 1
    op = enqueued[0]
    assert op.sink_name == "claims"
    assert op.payload["content"] == "Use Argon2 for password hashing"
    assert op.payload["confidence"] == "verified"
    assert op.payload["tags"] == ["decision"]
    assert op.payload["source_uuid"] == "agent:saw_record"
    # claim_uuid == op_id (idempotent dedup key)
    assert res["claim_uuid"] == op.op_id


def test_saw_record_no_write_queue():
    restore = _set_globals(_query_engine=None, _code_graph_engine=None, _write_queue=None)
    try:
        res = _run(at.saw_record(summary="x"))
    finally:
        restore()
    assert res["error"] == "write_queue_not_initialized"


def test_saw_record_empty_summary():
    class _WQ:
        def enqueue(self, ops):
            pass
    restore = _set_globals(_write_queue=_WQ())
    try:
        res = _run(at.saw_record(summary="   "))
    finally:
        restore()
    assert res["error"] == "empty_summary"
