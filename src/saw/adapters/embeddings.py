"""Embeddings adapter (M-19): real vector retrieval when ``sentence-transformers``
is installed, graceful fallback otherwise.

The FULL capability tier (``config/settings.py::detect_tier``) advertises FULL
only when embeddings are importable. Previously that check existed but no code
actually used embeddings (``adaptive_index`` said "in production, would use
embeddings") — the FULL tier was aspirational. This adapter provides the real
embed + greedy cosine clustering used by the learn engine; when the optional
dependency is absent, callers fall back to namespace/BM25 (LIGHTWEIGHT tier),
no silent stub.
"""
from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)

_ST_available: bool | None = None
_MODEL: Any = None


def embeddings_available() -> bool:
    """True if sentence-transformers is importable (enables FULL tier)."""
    global _ST_available
    if _ST_available is None:
        try:
            import sentence_transformers  # noqa: F401

            _ST_available = True
        except ImportError:
            _ST_available = False
    return _ST_available


def _get_model():
    """Lazy-load + cache a small sentence-transformers model."""
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Embed a batch of texts (L2-normalised).

    Returns None if embeddings are unavailable or the call failed — the caller
    must fall back to a non-semantic path.
    """
    if not embeddings_available() or not texts:
        return None
    try:
        model = _get_model()
        vecs = model.encode(texts, normalize_embeddings=True)
        return [list(v) for v in vecs]
    except Exception as e:  # model download failure, OOM, etc.
        logger.warning("Embedding failed, falling back to non-semantic: %s", e)
        return None


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two equal-length vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def cluster_by_embedding(
    texts: list[str], threshold: float = 0.65
) -> dict[int, list[int]]:
    """Greedy cluster *texts* by embedding cosine similarity.

    Returns ``{cluster_id: [text_index, ...]}``. Returns ``{}`` if embeddings
    are unavailable (caller falls back to namespace clustering).
    """
    vecs = embed_texts(texts)
    if vecs is None:
        return {}
    clusters: dict[int, list[int]] = {}
    centroids: list[list[float]] = []
    for i, v in enumerate(vecs):
        placed = False
        for cid, c in enumerate(centroids):
            if cosine_similarity(v, c) >= threshold:
                clusters[cid].append(i)
                members = clusters[cid]
                centroids[cid] = [
                    sum(vecs[j][k] for j in members) / len(members)
                    for k in range(len(v))
                ]
                placed = True
                break
        if not placed:
            centroids.append(list(v))
            clusters[len(centroids) - 1] = [i]
    return clusters
