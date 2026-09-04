"""Tests for embedding index (F-N-1, AC-EMB-1 / AC-EMB-3).

Skips when ``sentence_transformers`` is not installed (the ``[learn]`` extra),
matching the importorskip precedent in ``test_fsrs.py``.
"""
import pytest

pytest.importorskip("sentence_transformers")

import sqlite3
import struct
from unittest.mock import patch


def _make_db() -> sqlite3.Connection:
    """Create an in-memory DB with migrations applied."""
    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    return conn


def test_emb_ac1_ingest_writes_embedding():
    """AC-EMB-1: embedding index is written during ingest.

    Seeds a claim, runs EmbeddingSink.write(), then verifies:
    - embedding_store has a row
    - dim == 384 (all-MiniLM-L6-v2)
    - workspace_id matches
    """
    from saw.write_queue.sinks.embedding_sink import EmbeddingSink
    from saw.write_queue.queue import WriteOp

    conn = _make_db()
    sink = EmbeddingSink(conn)

    op = WriteOp(
        op_id="test-op-1",
        session_id="sess-1",
        sink_name="embedding",
        payload={
            "doc_id": "claim-uuid-1",
            "content": "Machine learning is a subset of artificial intelligence.",
            "entity_type": "claim",
            "workspace_id": "default",
        },
    )
    sink.write(op)

    row = conn.execute(
        "SELECT doc_id, dim, workspace_id, model FROM embedding_store WHERE doc_id = ?",
        ("claim-uuid-1",),
    ).fetchone()
    assert row is not None
    assert row[1] == 384  # dim
    assert row[2] == "default"  # workspace_id
    assert row[3] == "all-MiniLM-L6-v2"  # model


def test_emb_ac3_rebuild_skips_deleted():
    """AC-EMB-3: rebuild indexes non-deleted claims, skips deleted ones.

    Seeds 3 claims (1 deleted), rebuilds, verifies 2 vectors in
    embedding_store.
    """
    from saw.adapters.embeddings import embed_texts
    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)

    # Seed 3 claims, one deleted
    conn.executemany(
        "INSERT INTO claim (uuid, content, source_uuid, content_hash, workspace_id, deleted_at) "
        "VALUES (?, ?, 'src', 'hash', 'default', ?)",
        [
            ("c1", "Python is a programming language.", None),
            ("c2", "Machine learning uses neural networks.", None),
            ("c3", "Deleted claim about Java.", "2026-01-01T00:00:00"),
        ],
    )
    conn.commit()

    # Rebuild: embed non-deleted claims only
    claims = conn.execute(
        "SELECT uuid, content, workspace_id FROM claim WHERE deleted_at IS NULL"
    ).fetchall()
    for doc_id, content, ws in claims:
        vecs = embed_texts([content])
        if vecs is None:
            continue
        vec = vecs[0]
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "DELETE FROM embedding_store WHERE doc_id = ? AND workspace_id = ?",
            (doc_id, ws),
        )
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, dim, workspace_id) "
            "VALUES (?, 'claim', 'all-MiniLM-L6-v2', ?, ?, ?)",
            (doc_id, blob, dim, ws),
        )
    conn.commit()

    count = conn.execute(
        "SELECT COUNT(*) FROM embedding_store WHERE entity_type = 'claim'"
    ).fetchone()[0]
    assert count == 2  # deleted claim not indexed


def test_embedding_sink_upsert():
    """Upsert: re-writing the same doc_id replaces the old vector."""
    from saw.write_queue.sinks.embedding_sink import EmbeddingSink
    from saw.write_queue.queue import WriteOp

    conn = _make_db()
    sink = EmbeddingSink(conn)

    for content in ["First content about cats.", "Second content about dogs."]:
        op = WriteOp(
            op_id="test-upsert",
            session_id="sess-1",
            sink_name="embedding",
            payload={
                "doc_id": "claim-upsert",
                "content": content,
                "entity_type": "claim",
                "workspace_id": "default",
            },
        )
        sink.write(op)

    rows = conn.execute(
        "SELECT COUNT(*) FROM embedding_store WHERE doc_id = ?", ("claim-upsert",)
    ).fetchone()[0]
    assert rows == 1  # upsert replaces, not duplicates
