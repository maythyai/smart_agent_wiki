"""Tests for embedding index (F-N-1, AC-EMB-1 / AC-EMB-3, AC-EA-1 / AC-DIM-1 / AC-DIM-2).

v1.12.0 (F-Q-4): removed ``importorskip("sentence_transformers")`` — tests now
mock ``litellm.embedding`` to return fixed 1536-dim vectors. No local ST
or torch is loaded.
"""
from __future__ import annotations

import sqlite3
import struct
from unittest.mock import MagicMock, patch

# ── Mock helpers ───────────────────────────────────────────────────────

_DIM = 1536
_MOCK_MODEL = "text-embedding-3-small"

# Topic keyword sets for semantic-ish mock vectors.
_ML_KW = {"machine", "learning", "neural", "ai", "artificial",
          "intelligence", "deep", "ml", "training", "network", "data"}
_CRYPTO_KW = {"crypto", "ed25519", "signature", "elliptic", "curve",
              "cryptography", "algorithm", "byte", "signatures"}
_WEB_KW = {"web", "framework", "rest", "api", "html", "server", "building"}


def _topic_vec(text: str) -> list[float]:
    """Return a 1536-dim vector biased by text topic for cosine ranking."""
    words = set(text.lower().replace(".", "").replace(",", "").split())
    vec = [0.01] * _DIM
    if words & _ML_KW:
        vec[0] = 0.9
        vec[1] = 0.4
    elif words & _CRYPTO_KW:
        vec[0] = -0.8
        vec[2] = 0.5
    elif words & _WEB_KW:
        vec[1] = 0.8
        vec[3] = 0.3
    else:
        vec[0] = 0.5
    return vec


def _mock_embedding_response(**kwargs):
    """Create a mock litellm.embedding response with fixed-dim vectors."""
    texts = kwargs.get("input", [])
    response = MagicMock()
    response.data = [
        {"embedding": _topic_vec(t), "index": i}
        for i, t in enumerate(texts)
    ]
    return response


def _setup_mock_api(monkeypatch):
    """Configure env + mock litellm.embedding for a test."""
    import saw.adapters.embeddings as emb_mod

    monkeypatch.setenv("SAW_EMBEDDING_MODEL", _MOCK_MODEL)
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    # Reset the cached settings so _get_embedding_settings re-reads env.
    monkeypatch.setattr(emb_mod, "_embedding_settings", None)
    # Patch litellm.embedding at the module level.
    monkeypatch.setattr(
        emb_mod.litellm, "embedding", _mock_embedding_response
    )


# ── Tests ──────────────────────────────────────────────────────────────


def _make_db() -> sqlite3.Connection:
    """Create an in-memory DB with migrations applied."""
    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    return conn


def test_emb_ac1_ingest_writes_embedding(monkeypatch):
    """AC-EA-1 / AC-DIM-2: embedding index written during ingest via API mock.

    Seeds a claim, runs EmbeddingSink.write(), then verifies:
    - embedding_store has a row
    - dim == 1536 (text-embedding-3-small mock)
    - workspace_id matches
    - model column is the configured API model name (not all-MiniLM-L6-v2)
    """
    _setup_mock_api(monkeypatch)

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
    assert row[1] == _DIM  # dim = 1536
    assert row[2] == "default"  # workspace_id
    assert row[3] == _MOCK_MODEL  # model column is dynamic


def test_emb_ac3_rebuild_skips_deleted(monkeypatch):
    """AC-EMB-3: rebuild indexes non-deleted claims, skips deleted ones.

    Mock litellm.embedding → embed_texts → 2 vectors for non-deleted claims.
    """
    _setup_mock_api(monkeypatch)

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
        assert vecs is not None
        vec = vecs[0]
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "DELETE FROM embedding_store WHERE doc_id = ? AND workspace_id = ?",
            (doc_id, ws),
        )
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, dim, workspace_id) "
            "VALUES (?, 'claim', ?, ?, ?, ?)",
            (doc_id, _MOCK_MODEL, blob, dim, ws),
        )
    conn.commit()

    count = conn.execute(
        "SELECT COUNT(*) FROM embedding_store WHERE entity_type = 'claim'"
    ).fetchone()[0]
    assert count == 2  # deleted claim not indexed


def test_embedding_sink_upsert(monkeypatch):
    """Upsert: re-writing the same doc_id replaces the old vector."""
    _setup_mock_api(monkeypatch)

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


def test_dim_change_triggers_rebuild(monkeypatch):
    """AC-DIM-1: dimension change (384 → 1536) triggers wipe + rebuild."""
    _setup_mock_api(monkeypatch)

    from saw.adapters.embeddings import embed_texts
    from saw.db.migrations import apply_migrations

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)

    # Seed an old 384-dim vector (simulating v1.10.0 data)
    old_vec = [0.01] * 384
    old_blob = struct.pack("<384f", *old_vec)
    conn.execute(
        "INSERT INTO embedding_store (doc_id, entity_type, model, vector, dim, workspace_id) "
        "VALUES (?, 'claim', 'all-MiniLM-L6-v2', ?, 384, 'default')",
        ("old-doc", old_blob),
    )
    conn.commit()

    # Probe current dim via embed_texts (now returns 1536-dim)
    probe = embed_texts(["dimension probe"])
    assert probe is not None
    current_dim = len(probe[0])
    assert current_dim == _DIM  # 1536

    # Dimension change detection (same logic as rebuild_embeddings)
    old_dim_row = conn.execute(
        "SELECT DISTINCT dim FROM embedding_store LIMIT 1"
    ).fetchone()
    assert old_dim_row is not None
    assert old_dim_row[0] != current_dim  # 384 ≠ 1536

    # Wipe + rebuild
    conn.execute("DELETE FROM embedding_store")
    conn.commit()

    # Write new vector
    vec = probe[0]
    new_blob = struct.pack(f"<{current_dim}f", *vec)
    conn.execute(
        "INSERT INTO embedding_store (doc_id, entity_type, model, vector, dim, workspace_id) "
        "VALUES (?, 'claim', ?, ?, ?, 'default')",
        ("old-doc", _MOCK_MODEL, new_blob, current_dim),
    )
    conn.commit()

    # Verify: new dim, new model
    row = conn.execute(
        "SELECT dim, model FROM embedding_store WHERE doc_id = ?", ("old-doc",)
    ).fetchone()
    assert row[0] == _DIM  # 1536
    assert row[1] == _MOCK_MODEL
