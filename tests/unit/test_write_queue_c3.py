"""Tests for the C3 Write Queue hardening.

Covers:
- FTS5 atomic upsert (DELETE+INSERT in one transaction)
- FTS5Sink and WikiIndexer share the same transactional helper
- ContradictionsSink idempotent + transactional insert
- onboarding/timeline routes build valid WriteOps and enqueue atomically
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from saw.adapters.storage.claims_repository import CLAIMS_DB_SCHEMA
from saw.adapters.storage.fts5_utils import delete_fts_entry, upsert_fts_entry
from saw.domain.value_objects import (
    ContradictionType,
    ResolutionStrategy,
)
from saw.engines.govern.contradiction import ContradictionRecord
from saw.engines.query.wiki_indexer import WikiIndexer
from saw.write_queue.queue import OUTBOX_DDL, SQLiteWriteQueue, WriteOp
from saw.write_queue.sinks.contradictions_sink import (
    ContradictionsSink,
    store_contradiction,
)
from saw.write_queue.sinks.fts5_sink import FTS5Sink


# ── FTS5 atomic helpers ──────────────────────────────────────────────


def _conn_with_fts(tmp_path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(tmp_path / "t.db"))
    # fts_index table (mirrors claims_repository schema)
    conn.executescript(
        "CREATE VIRTUAL TABLE fts_index USING fts5("
        "title, content, tags, original UNINDEXED, tokenize='unicode61');"
    )
    return conn


class TestFTS5UpsertAtomic:
    def test_insert_then_update_replaces(self, tmp_path):
        conn = _conn_with_fts(tmp_path)
        upsert_fts_entry(conn, "page-a", "first content", tags="t1", original="first content")
        upsert_fts_entry(conn, "page-a", "second content", tags="t1", original="second content")
        rows = conn.execute("SELECT content FROM fts_index WHERE title='page-a'").fetchall()
        assert len(rows) == 1  # no duplicate
        assert "second" in rows[0][0]

    def test_delete_removes(self, tmp_path):
        conn = _conn_with_fts(tmp_path)
        upsert_fts_entry(conn, "page-b", "hello", tags="", original="hello")
        delete_fts_entry(conn, "page-b")
        assert conn.execute("SELECT 1 FROM fts_index WHERE title='page-b'").fetchall() == []


class TestFTS5SinkUsesHelper:
    def test_sink_write_is_atomic_upsert(self, tmp_path):
        conn = _conn_with_fts(tmp_path)
        sink = FTS5Sink(conn)
        op = WriteOp(op_id="op-1", session_id="s", sink_name="fts5",
                     payload={"doc_id": "d1", "title": "T", "content": "body", "tags": "x"})
        sink.write(op)
        sink.write(op)  # idempotent second write must not duplicate
        n = conn.execute("SELECT COUNT(*) FROM fts_index WHERE title='d1'").fetchone()[0]
        assert n == 1


class TestWikiIndexerUsesHelper:
    def test_index_and_remove(self, tmp_path):
        conn = _conn_with_fts(tmp_path)
        wiki = MagicMock()
        page = MagicMock()
        page.title = "Hello"
        page.content = "world body"
        page.tags = ["t1", "t2"]
        wiki.read.return_value = page
        wiki.list_pages.return_value = ["hello"]
        indexer = WikiIndexer(conn, wiki)
        assert indexer.index_all() == 1
        rows = conn.execute("SELECT title FROM fts_index").fetchall()
        assert rows == [("hello",)]
        indexer.remove_page("hello")
        assert conn.execute("SELECT 1 FROM fts_index").fetchall() == []


# ── Contradictions sink ─────────────────────────────────────────────


def _contradictions_conn(tmp_path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(tmp_path / "c.db"))
    conn.executescript(
        "CREATE TABLE claim (uuid TEXT PRIMARY KEY, content TEXT NOT NULL, "
        "source_uuid TEXT NOT NULL, page_number INTEGER, line_number INTEGER, "
        "timestamp TEXT, confidence TEXT NOT NULL DEFAULT 'unverified', "
        "source_mark TEXT NOT NULL DEFAULT 'extracted', tags TEXT NOT NULL DEFAULT '[]', "
        "entities TEXT NOT NULL DEFAULT '[]', content_hash TEXT NOT NULL, "
        "session_id TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')), "
        "updated_at TEXT, deleted_at TEXT); "
        "CREATE TABLE contradictions (uuid TEXT PRIMARY KEY, "
        "claim_a_uuid TEXT NOT NULL, claim_b_uuid TEXT NOT NULL, "
        "contradiction_type TEXT NOT NULL, resolution TEXT NOT NULL, "
        "detected_at TEXT NOT NULL, resolved_at TEXT, blast_radius TEXT);"
    )
    return conn


def _record(uuid="c-1", a="a1", b="b1") -> ContradictionRecord:
    return ContradictionRecord(
        uuid=uuid,
        claim_a_uuid=a,
        claim_b_uuid=b,
        contradiction_type=ContradictionType.FACTUAL,
        resolution=ResolutionStrategy.HISTORICAL,
        detected_at=datetime.now(timezone.utc),
        resolved_at=None,
        blast_radius=["page-x"],
    )


class TestContradictionsSink:
    def test_insert_idempotent(self, tmp_path):
        conn = _contradictions_conn(tmp_path)
        store_contradiction(conn, _record())
        store_contradiction(conn, _record())  # same uuid → ignored
        n = conn.execute("SELECT COUNT(*) FROM contradictions").fetchone()[0]
        assert n == 1

    def test_sink_write_from_payload(self, tmp_path):
        conn = _contradictions_conn(tmp_path)
        sink = ContradictionsSink(conn)
        from saw.write_queue.sinks.contradictions_sink import record_to_payload

        payload = record_to_payload(_record())
        op = WriteOp(op_id="op", session_id="s", sink_name="contradictions", payload=payload)
        sink.write(op)
        row = conn.execute("SELECT uuid, blast_radius FROM contradictions").fetchone()
        assert row[0] == "c-1"
        import json as _j
        assert _j.loads(row[1]) == ["page-x"]


class TestContradictionDetectorDelegates:
    def test_store_contradiction_uses_shared_helper(self, tmp_path):
        # Build a fake claims_repo exposing _conn backed by the schema.
        conn = _contradictions_conn(tmp_path)
        claims_repo = MagicMock()
        claims_repo._conn = conn

        from saw.engines.govern.contradiction import ContradictionDetector

        detector = ContradictionDetector.__new__(ContradictionDetector)
        detector._claims_repo = claims_repo
        detector._llm_router = MagicMock()
        detector._queue = None
        detector._processing = False
        detector._worker_task = None

        detector._store_contradiction(_record(uuid="c-det", a="aa", b="bb"))
        row = conn.execute("SELECT uuid FROM contradictions").fetchone()
        assert row == ("c-det",)


# ── Route enqueue contract (onboarding/timeline) ────────────────────


def _queue_conn(tmp_path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(tmp_path / "q.db"))
    conn.executescript(OUTBOX_DDL)
    return conn


class TestOnboardingEnqueueContract:
    def test_seed_enqueues_valid_writeops(self, tmp_path, monkeypatch):
        conn = _queue_conn(tmp_path)
        queue = SQLiteWriteQueue(conn)
        captured = []
        monkeypatch.setattr(queue, "enqueue_atomic", lambda ops: captured.append(ops))

        # Minimal starter kit
        from saw.drivers.web.routes import onboarding
        monkeypatch.setattr(onboarding, "STARTER_KITS", {
            "personal": {"name": "P", "pages": [
                {"slug": "welcome", "title": "Welcome", "content": "hi", "tags": ["intro"]},
            ]},
        })

        # Call the route handler directly with stub deps.
        import asyncio

        wiki_repo = MagicMock()
        wiki_repo.list_pages.return_value = []

        async def call():
            return await onboarding.seed_starter_kit(
                request=MagicMock(), kit_id="personal",
                wiki_repo=wiki_repo, write_queue=queue,
            )

        result = asyncio.run(call())
        assert result["pages_created"] == 1
        ops = captured[0]
        # Two ops (wiki + fts5), all valid WriteOps with required fields.
        assert len(ops) == 2
        for op in ops:
            assert isinstance(op, WriteOp)
            assert op.op_id and op.session_id == "onboarding"
            assert op.sink_name in ("wiki", "fts5")


class TestTimelineEnqueueContract:
    def test_daily_note_enqueues_valid_writeops(self, tmp_path, monkeypatch):
        conn = _queue_conn(tmp_path)
        queue = SQLiteWriteQueue(conn)
        captured = []
        monkeypatch.setattr(queue, "enqueue_atomic", lambda ops: captured.append(ops))

        from saw.drivers.web.routes import timeline
        from saw.drivers.web.schemas.timeline import DailyNoteRequest

        wiki_repo = MagicMock()
        wiki_repo.read.return_value = None  # does not exist → create

        import asyncio

        async def call():
            return await timeline.create_daily_note(
                request=DailyNoteRequest(date="2026-08-11"),
                wiki_repo=wiki_repo, write_queue=queue,
            )

        result = asyncio.run(call())
        assert result.status == "created"
        ops = captured[0]
        assert len(ops) == 2
        wiki_op = next(o for o in ops if o.sink_name == "wiki")
        assert wiki_op.payload["path"] == result.slug


class TestWriteQueueThreadSafety:
    """DEF-7: SQLiteWriteQueue must serialize all conn access under a lock.

    The production connection is opened with ``check_same_thread=False`` (see
    drivers/web/app.py) so the dispatcher thread and request threads share it.
    Without locking, concurrent commits raise ``sqlite3.OperationalError:
    database is locked`` or interleave writes.
    """

    def test_concurrent_enqueue_and_mark_done_no_corruption(self, tmp_path):
        import threading

        conn = sqlite3.connect(str(tmp_path / "cq.db"), check_same_thread=False)
        conn.executescript(OUTBOX_DDL)
        queue = SQLiteWriteQueue(conn)

        errors: list[Exception] = []

        def worker(i: int) -> None:
            try:
                ops = [
                    WriteOp(
                        op_id=f"op-{i}-{j}",
                        session_id="s",
                        sink_name="x",
                        payload={"i": i, "j": j},
                    )
                    for j in range(20)
                ]
                queue.enqueue(ops)
                for op in ops:
                    queue.mark_processing(op.op_id)
                    queue.track_sink(op.op_id, "x", "done")
                    queue.mark_done(op.op_id)
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"concurrent queue ops raised: {errors}"
        total = 8 * 20
        n = conn.execute("SELECT COUNT(*) FROM write_outbox").fetchone()[0]
        assert n == total
        done = conn.execute(
            "SELECT COUNT(*) FROM write_outbox WHERE status='done'"
        ).fetchone()[0]
        assert done == total
        tracked = conn.execute(
            "SELECT COUNT(*) FROM sink_tracking WHERE status='done'"
        ).fetchone()[0]
        assert tracked == total
