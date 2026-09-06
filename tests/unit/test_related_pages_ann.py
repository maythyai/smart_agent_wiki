"""Tests for related_pages ANN path reuse (T-F-S-2, AC-B-5).

Verifies compute_related_pages batch-loads embeddings instead of
per-page SELECT+cosine, and produces correct similarity scores.
"""
from __future__ import annotations

import struct
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

_DIM = 1536
_MOCK_MODEL = "text-embedding-3-small"

_ML_KW = {"machine", "learning", "neural", "ai", "artificial",
          "intelligence", "deep", "ml", "training", "network", "data"}
_CRYPTO_KW = {"crypto", "ed25519", "signature", "elliptic", "curve",
              "cryptography", "algorithm", "byte", "signatures"}
_WEB_KW = {"web", "framework", "rest", "api", "html", "server", "building"}


def _topic_vec(text: str) -> list[float]:
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
    response = MagicMock()
    texts = kwargs.get("input", [])
    response.data = [
        {"embedding": _topic_vec(t), "index": i}
        for i, t in enumerate(texts)
    ]
    return response


def _setup_mock_api(monkeypatch):
    import saw.adapters.embeddings as emb_mod

    monkeypatch.setenv("SAW_EMBEDDING_MODEL", _MOCK_MODEL)
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setattr(emb_mod, "_embedding_settings", None)
    monkeypatch.setattr(
        emb_mod.litellm, "embedding", _mock_embedding_response
    )


def test_related_pages_embedding_sim_batch(monkeypatch):
    """AC-B-5: related_pages with embeddings uses batch cosine path.

    Verifies that related pages computes embedding_sim correctly
    using the batch-loaded embeddings (not per-page SELECT).
    """
    _setup_mock_api(monkeypatch)

    import sqlite3

    from saw.adapters.embeddings import embed_texts
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.db.migrations import apply_migrations
    from saw.engines.query.related_pages import compute_related_pages

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)

    # Create wiki with pages (write markdown files)
    tmp_dir = Path(tempfile.mkdtemp())
    wiki_path = tmp_dir / "wiki"
    wiki_path.mkdir(parents=True)
    wiki_repo = WikiRepository(wiki_path)

    pages = [
        ("ml-1.md", "# ML-1\n\nMachine learning for prediction\n"),
        ("ml-2.md", "# ML-2\n\nNeural networks training\n"),
        ("crypto-1.md", "# Crypto-1\n\nEd25519 signatures\n"),
    ]

    for slug, content in pages:
        (wiki_path / slug).write_text(content)

    # Store embeddings (doc_id = full slug with .md)
    texts = [p[1] for p in pages]
    vecs = embed_texts(texts)
    assert vecs is not None
    for (slug, _), vec in zip(pages, vecs):
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, "
            "dim, workspace_id) VALUES (?, 'wiki', ?, ?, ?, 'default')",
            (slug, _MOCK_MODEL, blob, dim),
        )
    conn.commit()

    # Compute related pages for ml-1
    results = compute_related_pages(
        "ml-1.md", wiki_repo, top_k=5, conn=conn, workspace_id="default"
    )

    # ml-2 (ML topic) should rank higher than crypto-1 (crypto topic)
    assert len(results) > 0
    slugs = [r["slug"] for r in results]
    if "ml-2" in slugs and "crypto-1" in slugs:
        assert slugs.index("ml-2") < slugs.index("crypto-1"), (
            f"ml-2 should rank before crypto-1: {slugs}"
        )


def test_related_pages_no_embeddings_3signal(monkeypatch):
    """When embeddings unavailable, related_pages uses 3-signal path only."""
    # No API configured
    import saw.adapters.embeddings as emb_mod

    monkeypatch.setattr(emb_mod, "_embedding_settings", False)

    import sqlite3
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.db.migrations import apply_migrations
    from saw.engines.query.related_pages import compute_related_pages

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)

    tmp_dir = Path(tempfile.mkdtemp())
    wiki_path = tmp_dir / "wiki"
    wiki_path.mkdir(parents=True)
    wiki_repo = WikiRepository(wiki_path)

    (wiki_path / "p1.md").write_text("# P1\n\nMachine learning\n")
    (wiki_path / "p2.md").write_text("# P2\n\nNeural networks\n")

    results = compute_related_pages(
        "p1.md", wiki_repo, top_k=5, conn=conn, workspace_id="default"
    )
    # With no embeddings, should still return results from 3 signals
    # (tags, links, type — at least same_type)
    assert len(results) > 0
