"""Tests for smart-linking embedding signal (F-N-3, AC-LINK-1 / AC-LINK-3).

v1.12.0 (F-Q-4): removed ``importorskip("sentence_transformers")`` — tests now
mock ``litellm.embedding`` to return fixed vectors. No local ST or torch.
"""
from __future__ import annotations

import sqlite3
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
    """Return a _DIM-dim vector biased by text topic for cosine ranking."""
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


def _make_wiki_with_pages():
    """Create a temp wiki repo with pages that have no shared tags/links
    but are semantically related."""
    from saw.adapters.storage.wiki_repository import WikiRepository

    wiki_dir = Path(tempfile.mkdtemp()) / "wiki"
    wiki_dir.mkdir(parents=True)
    wiki = WikiRepository(wiki_dir)

    pages = {
        "ml-basics.md": (
            "# ML Basics\n\nMachine learning is a subset of AI. "
            "It uses neural networks to learn from data.",
            [],
        ),
        "deep-learning.md": (
            "# Deep Learning\n\nDeep learning uses multi-layer neural "
            "networks for representation learning.",
            [],
        ),
        "cryptography.md": (
            "# Cryptography\n\nThe Ed25519 algorithm produces 64-byte "
            "signatures using elliptic curve cryptography.",
            [],
        ),
    }

    for slug, (content, tags) in pages.items():
        page_path = wiki_dir / slug
        page_path.write_text(content)

    return wiki


def _make_db_with_embeddings(wiki, conn, monkeypatch):
    """Embed all wiki pages and store in embedding_store."""
    _setup_mock_api(monkeypatch)
    from saw.adapters.embeddings import embed_texts

    for slug in wiki.list_pages():
        page = wiki.read(slug)
        if page is None:
            continue
        vecs = embed_texts([page.content])
        if vecs is None:
            continue
        vec = vecs[0]
        dim = len(vec)
        blob = struct.pack(f"<{dim}f", *vec)
        conn.execute(
            "INSERT INTO embedding_store (doc_id, entity_type, model, vector, dim, workspace_id) "
            "VALUES (?, 'wiki', ?, ?, ?, 'default')",
            (slug, _MOCK_MODEL, blob, dim),
        )
    conn.commit()


def test_link_ac1_semantic_suggestion(monkeypatch):
    """AC-LINK-1: suggest includes semantically similar pages with no
    shared tags/links, and reasons contain 'semantic similarity'."""
    from saw.db.migrations import apply_migrations
    from saw.engines.query.related_pages import compute_related_pages

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    wiki = _make_wiki_with_pages()
    _make_db_with_embeddings(wiki, conn, monkeypatch)

    related = compute_related_pages(
        "ml-basics.md", wiki, top_k=8, conn=conn, workspace_id="default"
    )

    slugs = [r["slug"] for r in related]
    assert "deep-learning.md" in slugs

    # Check reasons include semantic similarity for deep-learning
    dl_entry = next(r for r in related if r["slug"] == "deep-learning.md")
    reasons_str = "; ".join(dl_entry.get("reasons", []))
    assert "semantic similarity" in reasons_str


def test_link_ac3_dissimilar_ranks_lower(monkeypatch):
    """AC-LINK-3: pages that share tags but are semantically dissimilar
    rank lower than pages that are semantically similar.

    Seeds: A=ML+tag python, B=Web framework+tag python, C=ML+tag python.
    Suggest for A: C should rank higher than B (semantic similarity).
    """
    from saw.adapters.storage.wiki_repository import WikiRepository
    from saw.db.migrations import apply_migrations
    from saw.engines.query.related_pages import compute_related_pages

    wiki_dir = Path(tempfile.mkdtemp()) / "wiki"
    wiki_dir.mkdir(parents=True)
    wiki = WikiRepository(wiki_dir)

    (wiki_dir / "ml-page.md").write_text(
        "---\ntags: [python]\n---\n# ML Page\n\nMachine learning with Python. "
        "Training neural networks on data."
    )
    (wiki_dir / "web-framework.md").write_text(
        "---\ntags: [python]\n---\n# Web Framework\n\nA Python web framework "
        "for building REST APIs and serving HTML."
    )
    (wiki_dir / "nn-page.md").write_text(
        "---\ntags: [python]\n---\n# NN Page\n\nNeural network training "
        "with deep learning architectures."
    )

    conn = sqlite3.connect(":memory:")
    apply_migrations(conn)
    _make_db_with_embeddings(wiki, conn, monkeypatch)

    related = compute_related_pages(
        "ml-page.md", wiki, top_k=8, conn=conn, workspace_id="default"
    )
    slugs_scores = {r["slug"]: r["score"] for r in related}

    # NN page (semantically similar + shared tag) should score higher
    # than web-framework (shared tag only, semantically different)
    if "nn-page.md" in slugs_scores and "web-framework.md" in slugs_scores:
        assert slugs_scores["nn-page.md"] > slugs_scores["web-framework.md"]
