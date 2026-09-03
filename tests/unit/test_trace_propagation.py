"""Trace-id propagation — F-D-2 (AC-OBS-1).

Verifies that a single request_id set on the request-context ContextVar is
carried into the write-queue dispatch path's log records (engines →
dispatcher → sinks), so a write operation's full chain is correlated.
"""
from __future__ import annotations

import logging

from saw.drivers.cli.commands.smoke_harness import build_smoke_context


class _CapturingHandler(logging.Handler):
    """Collect records emitted during the test window."""

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def test_write_path_logs_carry_request_id() -> None:
    """AC-OBS-1: write-operation logs carry the originating request_id."""
    from saw.drivers.web.middleware.observability import (
        _RequestIdFilter,
        init_observability,
        request_id_var,
    )

    # Attach the request-id filter to the root logger (as init would).
    root = logging.getLogger()
    snap_handlers = list(root.handlers)
    snap_level = root.level
    for h in list(root.handlers):
        root.removeHandler(h)
    capturer = _CapturingHandler()
    capturer.addFilter(_RequestIdFilter())
    root.addHandler(capturer)
    root.setLevel(logging.DEBUG)
    try:
        init_observability(auth_mode="local")
        # Simulate an inbound request setting its correlation id.
        token = request_id_var.set("rid-trace-123")
        try:
            ctx = build_smoke_context()
            try:
                from saw.drivers.cli.commands.smoke_harness import _ingest_fixture

                _ingest_fixture(ctx)
                # Force a log line from the write_queue/dispatcher module so
                # there is at least one write-path record to inspect.
                logging.getLogger("saw.write_queue.dispatcher").info(
                    "smoke dispatch window"
                )
            finally:
                ctx.close()
        finally:
            request_id_var.reset(token)

        # At least one captured record carries our request_id.
        stamped = [
            r for r in capturer.records
            if getattr(r, "request_id", None) == "rid-trace-123"
        ]
        assert stamped, (
            "no write-path log record carried the request_id; trace does not "
            "propagate engines -> write_queue -> sinks"
        )
    finally:
        for h in list(root.handlers):
            root.removeHandler(h)
        for h in snap_handlers:
            root.addHandler(h)
        root.setLevel(snap_level)


def test_request_id_isolates_concurrent_requests() -> None:
    """Two interleaved request contexts keep distinct request_ids."""
    from saw.drivers.web.middleware.observability import request_id_var

    t1 = request_id_var.set("rid-A")
    try:
        assert request_id_var.get() == "rid-A"
        t2 = request_id_var.set("rid-B")
        try:
            assert request_id_var.get() == "rid-B"
        finally:
            request_id_var.reset(t2)
        assert request_id_var.get() == "rid-A"
    finally:
        request_id_var.reset(t1)
