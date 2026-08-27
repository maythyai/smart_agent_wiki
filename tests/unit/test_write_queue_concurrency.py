"""Write-queue concurrency + crash-recovery tests (M-22).

Guards the HI-6 (CAS claim) and HI-7/HI-9 (recover stranded ops) fixes under
realistic concurrency — the existing write-queue tests cover single-threaded
happy paths only.
"""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone

import pytest

from saw.domain.value_objects import WriteOpStatus
from saw.write_queue.dispatcher import Dispatcher
from saw.write_queue.queue import SQLiteWriteQueue, WriteOp


def _queue() -> SQLiteWriteQueue:
    # check_same_thread=False: the dispatcher runs in worker threads; the
    # production conn uses this flag too.
    return SQLiteWriteQueue(sqlite3.connect(":memory:", check_same_thread=False))


def _op(op_id: str, sink: str = "wiki") -> WriteOp:
    return WriteOp(
        op_id=op_id,
        session_id="s",
        sink_name=sink,
        payload={},
        status=WriteOpStatus.PENDING,
        created_at=datetime.now(timezone.utc),
    )


# ── HI-6: CAS prevents double-claim under concurrent dispatch ──────


def test_concurrent_dispatch_does_not_double_execute():
    """Two dispatchers racing the same pending op must execute it exactly once."""
    q = _queue()
    q.enqueue([_op("race-1")])

    executed: list[str] = []
    lock = threading.Lock()

    class CountingSink:
        name = "wiki"

        def write(self, op) -> None:
            with lock:
                executed.append(op.op_id)

    # Two dispatchers over the SAME queue+sink (simulates two workers).
    d1 = Dispatcher(q, sinks=[CountingSink()])
    d2 = Dispatcher(q, sinks=[CountingSink()])

    barrier = threading.Barrier(2)

    def run(d: Dispatcher) -> None:
        barrier.wait()
        d.dispatch_pending()

    t1 = threading.Thread(target=run, args=(d1,))
    t2 = threading.Thread(target=run, args=(d2,))
    t1.start(); t2.start(); t1.join(); t2.join()

    # The op must be executed exactly once despite the race.
    assert executed.count("race-1") == 1, f"executed {executed.count('race-1')}x: {executed}"


def test_many_ops_two_dispatchers_no_duplication():
    """10 ops, 2 racing dispatchers → each executed at most once."""
    q = _queue()
    for i in range(10):
        q.enqueue([_op(f"op-{i}")])

    executed: list[str] = []
    lock = threading.Lock()

    class CountingSink:
        name = "wiki"

        def write(self, op) -> None:
            with lock:
                executed.append(op.op_id)

    d1 = Dispatcher(q, sinks=[CountingSink()])
    d2 = Dispatcher(q, sinks=[CountingSink()])
    barrier = threading.Barrier(2)

    def run(d):
        barrier.wait()
        for _ in range(5):  # loop to drain
            d.dispatch_pending()

    threads = [threading.Thread(target=run, args=(d1,)), threading.Thread(target=run, args=(d2,))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(executed) == 10, f"expected 10, got {len(executed)}: {executed}"
    assert len(set(executed)) == 10, f"duplicates: {executed}"


# ── HI-7/HI-9: crash recovery ──────────────────────────────────────


def test_recover_resets_stranded_processing_ops():
    """An op left in 'processing' by a crash is reset to 'pending' by recover()."""
    q = _queue()
    q.enqueue([_op("stranded")])
    assert q.mark_processing("stranded") is True  # claim it
    # Simulate a crash: op stays 'processing', never mark_done.
    pending_before = q.get_pending()
    assert pending_before == [], "processing op must not appear in get_pending"

    d = Dispatcher(q)  # no sinks needed for recover()
    recovered = d.recover()
    assert recovered == 1

    pending_after = q.get_pending()
    assert len(pending_after) == 1 and pending_after[0].op_id == "stranded"


def test_recover_is_idempotent():
    """recover() on a queue with no processing ops is a no-op (0)."""
    q = _queue()
    q.enqueue([_op("p1")])
    d = Dispatcher(q)
    assert d.recover() == 0
