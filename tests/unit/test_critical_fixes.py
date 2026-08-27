"""Regression tests for the Critical/High architecture-audit fixes.

Locks in the behaviour of:
- CR-1: ApiKey header is verified against the DB (no blind admin trust)
- CR-3: enqueue_atomic dispatches via an attached dispatcher
- HI-6: mark_processing CAS guard prevents double-claim
- HI-8: _eval_condition returns a native bool (was always truthy)
- HI-12: SSRF guard blocks internal/non-http targets

These tests guard against the regressions documented in
ARCHITECTURE_REVIEW.md (M-21/M-22 — no architecture/concurrency guards).
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import pytest


# ── CR-3 + HI-6: write queue dispatch + CAS ───────────────────────────


def _make_queue():
    from saw.write_queue.queue import SQLiteWriteQueue

    return SQLiteWriteQueue(sqlite3.connect(":memory:"))


def _make_op(op_id="op1", sink="wiki"):
    from saw.domain.value_objects import WriteOpStatus
    from saw.write_queue.queue import WriteOp

    return WriteOp(
        op_id=op_id,
        session_id="s",
        sink_name=sink,
        payload={},
        status=WriteOpStatus.PENDING,
        created_at=datetime.now(timezone.utc),
    )


def test_enqueue_atomic_dispatches_via_attached_dispatcher():
    """CR-3: enqueue_atomic must drain to sinks, not silently enqueue."""
    q = _make_queue()
    dispatched = []

    class FakeDispatcher:
        def dispatch_pending(self):
            dispatched.append(True)

    q.attach_dispatcher(FakeDispatcher())
    q.enqueue_atomic([_make_op()])
    assert dispatched, "enqueue_atomic did not invoke dispatch_pending"


def test_mark_processing_cas_rejects_double_claim():
    """HI-6: a second mark_processing on an already-processing op must fail."""
    q = _make_queue()
    q.enqueue([_make_op("cas1")])
    assert q.mark_processing("cas1") is True
    assert q.mark_processing("cas1") is False  # already claimed


# ── HI-8: workflow condition evaluation ───────────────────────────────


def test_eval_condition_returns_native_false():
    """HI-8: a false condition must skip (previously bool('False') == True)."""
    from saw.engines.collaborate.workflow_executor import WorkflowExecutor

    we = WorkflowExecutor.__new__(WorkflowExecutor)
    assert we._eval_condition("1 > 2", {}) is False
    assert we._eval_condition("2 > 1", {}) is True
    assert we._eval_condition("confidence > 3", {"confidence": 1}) is False
    assert we._eval_condition("confidence > 3", {"confidence": 5}) is True


# ── HI-12: SSRF guard ─────────────────────────────────────────────────


def test_ssrf_guard_blocks_internal_targets():
    from saw.adapters.url_guard import assert_safe_url, SsrfError

    blocked = [
        "http://169.254.169.254/latest/meta-data/",
        "http://127.0.0.1:8000/api/x",
        "http://10.0.0.1/",
        "http://192.168.1.1/",
        "ftp://example.com/",
    ]
    for url in blocked:
        with pytest.raises(SsrfError):
            assert_safe_url(url)

    # Public host must pass.
    assert_safe_url("https://example.com/")


# ── CR-1: ApiKey auth is verified, not trusted ────────────────────────


class _FakeRequest:
    def __init__(self, auth_header, mode="team"):
        self.headers = {"Authorization": auth_header} if auth_header else {}
        self.app = type("App", (), {"state": type("S", (), {"auth_mode": mode})()})()


def test_apikey_header_rejected_when_not_in_db(monkeypatch):
    """CR-1: an ApiKey header for a key not in the DB must 401, not admin."""
    import saw.api.keys as keys_mod

    # Force the DB lookup to return None (no key registered). The auth
    # dependency imports verify_api_key_sync from saw.api.keys at call time.
    monkeypatch.setattr(keys_mod, "verify_api_key_sync", lambda _k: None)
    from saw.drivers.web.middleware.security import get_current_user_from_token

    with pytest.raises(Exception) as exc:
        get_current_user_from_token(_FakeRequest("ApiKey x"))
    assert getattr(exc.value, "status_code", None) == 401


# ── HI-2: in-memory event bus + WebSocket dict-event mapping ─────────


def test_event_bus_publish_and_subscribe():
    """HI-2: publish (async + sync) reaches async-iterator subscribers."""
    import asyncio

    from saw.plugins.event_bus import InMemoryEventBus

    async def main():
        bus = InMemoryEventBus()
        received = []
        sub = bus.subscribe()

        async def consume():
            async for evt in sub:
                received.append(evt)
                if len(received) >= 2:
                    break

        task = asyncio.create_task(consume())
        await bus.publish({"type": "WorkflowStarted", "name": "litreview"})
        bus.publish_nowait({"type": "PageUpdated", "sink": "wiki", "slug": "x"})
        await asyncio.sleep(0.05)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        assert [r["type"] for r in received] == ["WorkflowStarted", "PageUpdated"]

    asyncio.run(main())


def test_event_bus_handler_callback():
    """HI-2: add_subscriber fires for matching + all-events handlers."""
    import asyncio

    from saw.plugins.event_bus import InMemoryEventBus

    async def main():
        bus = InMemoryEventBus()
        hits = []
        bus.add_subscriber("WorkflowStep", lambda e: hits.append(("typed", e["type"])))
        bus.add_subscriber(None, lambda e: hits.append(("all", bus._event_name(e))))
        await bus.publish({"type": "WorkflowStep", "step": 1})
        await bus.publish({"type": "PageUpdated", "slug": "y"})
        assert ("typed", "WorkflowStep") in hits
        assert ("all", "WorkflowStep") in hits
        assert ("all", "PageUpdated") in hits

    asyncio.run(main())


def test_websocket_dict_event_mapping():
    """HI-2: WS manager maps dict events (WorkflowExecutor/Dispatcher path)."""
    from saw.drivers.web.websocket import ConnectionManager

    m = ConnectionManager()
    step = m._event_to_message({"type": "WorkflowStep", "workflow": "ingest", "step": 1})
    assert step.type == "workflow_progress"
    assert step.payload == {"workflow": "ingest", "step": 1}

    page = m._event_to_message({"type": "PageUpdated", "sink": "wiki", "slug": "home"})
    assert page.type == "page_updated"
    assert page.payload["slug"] == "home"


# ── HI-1: repository methods replace route-level raw SQL ─────────────


def test_claims_repository_methods_replace_inline_sql():
    """HI-1: update_confidence / soft_delete / contradictions live in the repo."""
    import sqlite3

    from saw.adapters.storage.claims_repository import SQLiteClaimsRepository
    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    repo = SQLiteClaimsRepository(conn)
    conn.execute(
        "INSERT INTO claim(uuid,content,source_uuid,content_hash) VALUES(?,?,?,?)",
        ("c1", "x", "s1", "h1"),
    )
    conn.commit()
    repo.update_confidence("c1", "cross_validated")
    row = conn.execute(
        "SELECT confidence, updated_at FROM claim WHERE uuid=?", ("c1",)
    ).fetchone()
    assert row[0] == "cross_validated" and row[1] is not None
    repo.soft_delete_claim("c1")
    assert repo.count() == 0
    assert repo.count_relations("c1") == 0
    assert repo.list_contradictions("pending") == []


# ── HI-5: connector bootstrap registers connectors (no 404) ─────────


def test_connector_bootstrap_populates_registry():
    """HI-5: register_default_connectors populates the singleton registry."""
    from saw.connectors.bootstrap import register_default_connectors
    from saw.connectors.registry import ConnectorRegistry

    ConnectorRegistry.reset()
    reg = ConnectorRegistry()
    registered = register_default_connectors(reg)
    assert registered, "no connectors registered"
    for platform in registered:
        assert reg.get(platform) is not None, f"{platform} still 404 after register"


# ── HI-9: workflow execution persistence + stranded recovery ────────


def test_workflow_persistence_and_recovery():
    """HI-9: workflow state persists; stranded 'running' rows recover on startup."""
    import sqlite3

    from saw.db.migrations import apply_migrations
    from saw.drivers.web.app import _recover_stranded_workflows
    from saw.engines.collaborate.workflow_executor import WorkflowExecutor

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    we = WorkflowExecutor.__new__(WorkflowExecutor)
    we._conn = conn
    # running -> completed upsert
    we._persist_workflow("w1", "lit", "running", 0, 3, [])
    we._persist_workflow("w1", "lit", "completed", 3, 3, [])
    row = conn.execute(
        "SELECT status, steps_completed FROM workflow_executions WHERE workflow_id=?",
        ("w1",),
    ).fetchone()
    assert row == ("completed", 3)
    # a stranded 'running' workflow is recovered to 'interrupted'
    we._persist_workflow("w2", "ingest", "running", 1, 5, [])
    n = _recover_stranded_workflows(conn)
    assert n == 1, n
    status = conn.execute(
        "SELECT status FROM workflow_executions WHERE workflow_id=?", ("w2",)
    ).fetchone()[0]
    assert status == "interrupted"


# ── M-6: HTTPException reshaped to RFC 7807; 5xx detail masked ──────


def test_http_exception_rfc7807_and_5xx_masking():
    """M-6: HTTPException returns RFC 7807; 4xx detail kept, 5xx masked."""
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient

    from saw.drivers.web.middleware.errors import register_exception_handlers

    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/e4")
    def e4():
        raise HTTPException(status_code=404, detail="not found here")

    @app.get("/e5")
    def e5():
        raise HTTPException(status_code=500, detail="internal: secret=XYZ")

    c = TestClient(app)
    r = c.get("/e4")
    assert r.status_code == 404
    body = r.json()
    assert body["type"].endswith("http-404") and body["detail"] == "not found here"
    r2 = c.get("/e5")
    assert r2.status_code == 500
    assert r2.json()["detail"] == "An internal error occurred"
    assert "XYZ" not in r2.text  # no internal leak


# ── M-24/M-25: WeCom constant-time compare + replay window ──────────


def test_wecom_constant_time_and_replay_protection():
    """M-24: compare_digest (not ==); M-25: reject stale timestamps."""
    import base64
    import hashlib
    import time

    from saw.connectors.im.wecom.crypto import WeComCrypto

    aes_key = base64.b64encode(b"\x00" * 32).decode().rstrip("=")
    crypto = WeComCrypto(encoding_aes_key=aes_key, token="tok", corp_id="corp")
    ts = str(int(time.time()))
    nonce, encrypted = "n", "enc"
    good_sig = hashlib.sha1(
        "".join(sorted(["tok", ts, nonce, encrypted])).encode()
    ).hexdigest()
    assert crypto.verify_signature(good_sig, ts, nonce, encrypted) is True
    # wrong signature rejected
    assert crypto.verify_signature("0" * 40, ts, nonce, encrypted) is False
    # stale timestamp rejected (replay protection)
    stale_ts = str(int(time.time()) - 600)
    stale_sig = hashlib.sha1(
        "".join(sorted(["tok", stale_ts, nonce, encrypted])).encode()
    ).hexdigest()
    assert crypto.verify_signature(stale_sig, stale_ts, nonce, encrypted) is False


# ── M-26: webhook signing secret encrypted at rest ──────────────────


def test_webhook_secret_encrypted_at_rest(monkeypatch):
    """M-26: Fernet encrypts/decrypts the webhook signing secret."""
    from cryptography.fernet import Fernet

    monkeypatch.setenv("SAW_ENCRYPTION_KEY", Fernet.generate_key().decode())
    from saw.connectors.token_encryption import TokenEncryption

    enc = TokenEncryption.from_env()
    secret = "s_" + "a" * 30
    stored = enc.encrypt(secret)
    assert stored != secret  # actually encrypted, not plaintext
    assert enc.decrypt(stored) == secret  # round-trips


# ── M-18: version derived from package metadata ─────────────────────


def test_version_derived_from_metadata():
    """M-18: __version__ comes from importlib.metadata, not a hardcode."""
    from saw.drivers.web.app import __version__

    try:
        from importlib.metadata import version as _pkg_version

        expected = _pkg_version("smart-agent-wiki")
    except Exception:
        expected = None
    assert __version__
    if expected:
        assert __version__ == expected


# ── M-13: FK indexes on graph tables (migration v5) ─────────────────


def test_migration_v5_adds_graph_fk_indexes():
    """M-13: claim_relation/entity_relation/contradictions FK indexes exist."""
    import sqlite3

    from saw.db.migrations import apply_migrations, get_version

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    assert get_version(conn) >= 5
    idx = {
        r[1]
        for r in conn.execute("SELECT * FROM sqlite_master WHERE type='index'").fetchall()
    }
    for n in (
        "idx_claim_relation_source",
        "idx_claim_relation_target",
        "idx_entity_relation_source",
        "idx_entity_relation_target",
        "idx_contradictions_resolved",
    ):
        assert n in idx, f"missing index {n}"


# ── M-28: CJK-aware code graph FTS search ─────────────────────────────


def test_code_graph_fts_cjk_search():
    """M-28: CJK code-node names are searchable (was bare unicode61 → no match)."""
    import os
    import tempfile

    from saw.code_graph.models import CodeNode, NodeKind
    from saw.code_graph.store import CodeGraphStore

    store = CodeGraphStore(os.path.join(tempfile.mkdtemp(), "cg.db"))
    store.upsert_node(
        CodeNode(
            uid="cjk1",
            name="用户管理",
            kind=NodeKind.FUNCTION,
            file_path="app.py",
            language="python",
            content_hash="h",
            metadata={},
        )
    )
    store.upsert_node(
        CodeNode(
            uid="en1",
            name="get_users",
            kind=NodeKind.FUNCTION,
            file_path="app.py",
            language="python",
            content_hash="h2",
            metadata={},
        )
    )
    cjk_hits = [n.name for n in store.search_nodes_fts("用户管理")]
    assert "用户管理" in cjk_hits, f"CJK search failed: {cjk_hits}"
    en_hits = [n.name for n in store.search_nodes_fts("get_users")]
    assert "get_users" in en_hits


# ── M-19: embeddings adapter degrades gracefully ───────────────────


def test_embeddings_adapter_fallback_and_math():
    """M-19: cosine math correct; embed/cluster degrade when dep absent."""
    from saw.adapters.embeddings import (
        cluster_by_embedding,
        cosine_similarity,
        embed_texts,
        embeddings_available,
    )

    assert isinstance(embeddings_available(), bool)
    # cosine_similarity is pure math (always works).
    assert abs(cosine_similarity([1, 0], [1, 0]) - 1.0) < 1e-9
    assert abs(cosine_similarity([1, 0], [0, 1])) < 1e-9
    # Without sentence-transformers installed these return None / {} (no crash).
    if not embeddings_available():
        assert embed_texts(["hello"]) is None
        assert cluster_by_embedding(["a", "b"]) == {}


# ── M-14: on_failure="rollback" rejected at parse ───────────────────


def test_workflow_rollback_rejected_at_parse(tmp_path):
    """M-14: 'rollback' is advertised but unimplemented — reject at parse."""
    from saw.engines.collaborate.workflow_parser import (
        WorkflowParseError,
        WorkflowParser,
    )

    p = tmp_path / "w.yaml"
    p.write_text(
        "name: t\n"
        "steps:\n"
        "  - agent: Writer\n"
        "    action: write\n"
        "on_failure: rollback\n"
    )
    with pytest.raises(WorkflowParseError, match="rollback"):
        WorkflowParser().parse(p)
