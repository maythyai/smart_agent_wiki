"""Contradictions sink - persists detected contradictions to the Claims DB.

C3: the ``ContradictionDetector`` previously wrote to the ``contradictions``
table directly, bypassing any retry/dedup/tracking. This sink is the
single source of truth for that INSERT so that:

* the write is transactional (``with conn:``),
* it is idempotent (``INSERT OR IGNORE`` on the uuid primary key),
* the same code path is used whether the detector writes synchronously
  or — as a future extension — the write is routed through the Write
  Queue outbox by enqueuing a WriteOp with ``sink_name='contradictions'``.

The contradiction detector is the only current caller; it still writes
directly (the contradictions table lives in the claims DB and the
detection runs async/best-effort). Routing through the outbox is a
documented future option — the sink's ``write(op)`` contract already
matches what the outbox dispatcher would call.
"""
from __future__ import annotations

import json
import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from saw.engines.govern.contradiction import ContradictionRecord


_CONTRADICTION_INSERT = """INSERT OR IGNORE INTO contradictions
    (uuid, claim_a_uuid, claim_b_uuid, contradiction_type,
     resolution, detected_at, resolved_at, blast_radius)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""


def record_to_payload(record: "ContradictionRecord") -> dict:
    """Serialise a ContradictionRecord to a sink payload dict."""
    return {
        "uuid": record.uuid,
        "claim_a_uuid": record.claim_a_uuid,
        "claim_b_uuid": record.claim_b_uuid,
        "contradiction_type": record.contradiction_type.name.lower(),
        "resolution": record.resolution.name.lower(),
        "detected_at": record.detected_at.isoformat(),
        "resolved_at": record.resolved_at.isoformat() if record.resolved_at else None,
        "blast_radius": record.blast_radius,
    }


def store_contradiction(conn: sqlite3.Connection, record: "ContradictionRecord") -> None:
    """Persist a contradiction record (idempotent, transactional)."""
    payload = record_to_payload(record)
    with conn:
        conn.execute(
            _CONTRADICTION_INSERT,
            (
                payload["uuid"],
                payload["claim_a_uuid"],
                payload["claim_b_uuid"],
                payload["contradiction_type"],
                payload["resolution"],
                payload["detected_at"],
                payload["resolved_at"],
                json.dumps(payload["blast_radius"]),
            ),
        )


class ContradictionsSink:
    """Write Queue sink for the contradictions table."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @property
    def name(self) -> str:
        return "contradictions"

    def write(self, op) -> None:
        """Insert a contradiction row from a WriteOp payload (idempotent)."""
        payload = op.payload
        with self._conn:
            self._conn.execute(
                _CONTRADICTION_INSERT,
                (
                    payload.get("uuid", op.op_id),
                    payload["claim_a_uuid"],
                    payload["claim_b_uuid"],
                    payload["contradiction_type"],
                    payload["resolution"],
                    payload["detected_at"],
                    payload.get("resolved_at"),
                    json.dumps(payload.get("blast_radius", [])),
                ),
            )

    def can_handle(self, sink_name: str) -> bool:
        return sink_name == "contradictions"
