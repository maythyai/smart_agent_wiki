"""Embedding sink - persists claim/wiki embedding vectors for semantic search.

Per ADR-010: vectors are stored as BLOB (struct.pack float32 arrays) in the
``embedding_store`` table, retrieved as full-table cosine similarity for
top-K ranking.  Follows the FTS5Sink paradigm (``write(op)`` +
``can_handle(sink_name)`` + ``name`` property).

When sentence-transformers is not installed (tier < FULL), ``write()``
silently skips — no error, no partial write. This matches the degradation
contract in PMS-embedding: non-FULL tiers are unaffected.
"""
from __future__ import annotations

import logging
import sqlite3
import struct

from saw.adapters.embeddings import embed_texts, embeddings_available

logger = logging.getLogger(__name__)


class EmbeddingSink:
    """Write Queue sink for embedding vector persistence."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    @property
    def name(self) -> str:
        return "embedding"

    def write(self, op) -> None:
        """Generate + persist an embedding vector for a claim/wiki write op.

        Skips silently when embeddings are unavailable (tier < FULL) or when
        embedding generation fails — the caller's ingest pipeline continues
        normally (FTS5 / claims sinks still complete).
        """
        payload = op.payload
        doc_id = payload.get("doc_id") or payload.get("claim_uuid") or op.op_id
        content = payload.get("content", "")
        workspace_id = payload.get("workspace_id", "default")
        entity_type = payload.get("entity_type", "claim")

        # Tier check: skip if embeddings unavailable (tier < FULL)
        if not embeddings_available():
            logger.info("embeddings unavailable, skipping vector index")
            return

        vecs = embed_texts([content])
        if vecs is None:
            logger.warning("Embedding failed for %s, skipping", doc_id)
            return

        vec = vecs[0]
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)

        # Upsert (DELETE + INSERT pattern, same as FTS5Sink)
        self._conn.execute(
            "DELETE FROM embedding_store WHERE doc_id = ? AND workspace_id = ?",
            (doc_id, workspace_id),
        )
        self._conn.execute(
            """INSERT INTO embedding_store
               (doc_id, entity_type, model, vector, dim, workspace_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (doc_id, entity_type, "all-MiniLM-L6-v2", blob, dim, workspace_id),
        )

    def can_handle(self, sink_name: str) -> bool:
        return sink_name == "embedding"
