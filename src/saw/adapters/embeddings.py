"""Embeddings adapter: litellm API (primary) + local ST (optional fallback).

v1.12.0 (ADR-012): embedding provider pivoted from local sentence-transformers
to litellm OpenAI-style API.  The local ST path is preserved as an optional
fallback for users who have the ``[learn]`` extra installed but no API key.

Provider priority: API (litellm.embedding) → local ST → None (degrade to BM25).

The ``embed_texts(texts) -> list[list[float]] | None`` signature is unchanged
from v1.10.0 — downstream callers (EmbeddingSink, QueryEngine,
compute_related_pages) require no modifications.
"""
from __future__ import annotations

import logging
import math
import os
from typing import Any

import litellm

logger = logging.getLogger(__name__)

# ── Local ST fallback state (preserved from v1.10.0) ──────────────────
_ST_available: bool | None = None
_MODEL: Any = None

# ── API embedding settings (lazy-loaded) ───────────────────────────────
_embedding_settings: Any = None  # EmbeddingSettings | None


def _get_embedding_settings() -> Any:
    """Lazy-load embedding settings from environment variables.

    Returns an ``EmbeddingSettings`` instance or ``None`` when no embedding
    model is configured (neither env var nor config file).

    Env vars (same pattern as LLMRouter):
    - SAW_EMBEDDING_MODEL / EMBEDDING_MODEL: model name
    - EMBEDDING_API_KEY / SAW_EMBEDDING_API_KEY: API key (fallback: OPENAI_API_KEY)
    - SAW_EMBEDDING_API_BASE / OPENAI_BASE_URL: custom endpoint
    - SAW_EMBEDDING_TIMEOUT: per-call timeout (default 60)
    """
    global _embedding_settings
    if _embedding_settings is not None:
        return _embedding_settings

    model = (
        os.environ.get("SAW_EMBEDDING_MODEL")
        or os.environ.get("EMBEDDING_MODEL", "")
    )
    if not model:
        _embedding_settings = False  # sentinel: "checked, not configured"
        return None

    api_key = (
        os.environ.get("EMBEDDING_API_KEY")
        or os.environ.get("SAW_EMBEDDING_API_KEY")
        or os.environ.get("OPENAI_API_KEY", "")
    )
    api_base = (
        os.environ.get("SAW_EMBEDDING_API_BASE")
        or os.environ.get("OPENAI_BASE_URL", "")
    )
    timeout_str = os.environ.get("SAW_EMBEDDING_TIMEOUT", "60")

    try:
        from saw.config.settings import EmbeddingSettings

        _embedding_settings = EmbeddingSettings(
            model=model,
            api_key=api_key,
            api_base=api_base,
            timeout=int(timeout_str),
        )
    except Exception:
        _embedding_settings = False
        return None
    return _embedding_settings


def _api_embedding_available() -> bool:
    """True if embedding API is configured (model + api_key or api_base)."""
    cfg = _get_embedding_settings()
    if cfg is None or cfg is False:
        return False
    if not cfg.model:
        return False
    # api_base configured → assume reachable (same as router.py _check_available)
    if cfg.api_base:
        return True
    # Check API key
    if cfg.api_key:
        return True
    return False


def _st_available() -> bool:
    """True if sentence-transformers is importable (local ST fallback)."""
    global _ST_available
    if _ST_available is None:
        try:
            import sentence_transformers  # noqa: F401

            _ST_available = True
        except ImportError:
            _ST_available = False
    return _ST_available


def _get_model():
    """Lazy-load + cache a small sentence-transformers model (fallback)."""
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def _normalize(vec: list[float]) -> list[float]:
    """L2-normalize a vector (same as SentenceTransformer normalize_embeddings=True)."""
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


def _embed_via_api(texts: list[str]) -> list[list[float]] | None:
    """Embed texts via litellm.embedding API (primary provider).

    Calls ``litellm.embedding`` with model/input/api_base/api_key from
    EmbeddingSettings, following the same call pattern as ``router.py``
    ``_completion_with_retry`` (litellm.completion).
    """
    cfg = _get_embedding_settings()
    if cfg is None or cfg is False:
        return None
    try:
        kwargs: dict[str, Any] = {
            "model": cfg.model,
            "input": texts,
            "timeout": cfg.timeout,
        }
        if cfg.api_base:
            kwargs["api_base"] = cfg.api_base
        if cfg.api_key:
            kwargs["api_key"] = cfg.api_key

        response = litellm.embedding(**kwargs)
        # litellm embedding response: response.data[i]["embedding"]
        vecs = [item["embedding"] for item in response.data]
        # L2-normalize (SentenceTransformer normalize_embeddings=True equivalent)
        return [_normalize(v) for v in vecs]
    except Exception as e:
        logger.warning("API embedding failed, falling back: %s", e)
        return None


def _embed_via_st(texts: list[str]) -> list[list[float]] | None:
    """Embed via local SentenceTransformer (fallback path, v1.10.0 preserved)."""
    if not _st_available() or not texts:
        return None
    try:
        model = _get_model()
        vecs = model.encode(texts, normalize_embeddings=True)
        return [list(v) for v in vecs]
    except Exception as e:
        logger.warning("Local ST embedding failed: %s", e)
        return None


def embeddings_available() -> bool:
    """True if any embedding provider is available (API OR local ST).

    Used by detect_tier() to set FULL tier.
    - API configured (EmbeddingSettings has model + api_key or api_base) → True
    - Local ST importable ([learn] extra installed) → True
    - Neither → False (tier=LIGHTWEIGHT, semantic endpoints degrade to BM25)
    """
    return _api_embedding_available() or _st_available()


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Embed a batch of texts (L2-normalised).

    Provider priority: API (litellm.embedding) > local ST > None.
    Returns None if all providers fail — the caller must fall back to a
    non-semantic path (BM25).

    Signature unchanged from v1.10.0 — downstream callers need no modifications.
    """
    if not texts:
        return None

    # 1. Try API (primary path, default for v1.12.0)
    if _api_embedding_available():
        vecs = _embed_via_api(texts)
        if vecs is not None:
            return vecs
        logger.warning("API embedding failed, trying local ST fallback")

    # 2. Try local ST fallback (v1.10.0 path, preserved for backward compat)
    if _st_available():
        logger.info("API unavailable, falling back to local ST")
        vecs = _embed_via_st(texts)
        if vecs is not None:
            return vecs

    # 3. All providers failed
    return None


def _current_model_name() -> str:
    """Get current embedding model name for the model column.

    Returns the configured API model name, or falls back to
    ``all-MiniLM-L6-v2`` when only local ST is available.
    """
    cfg = _get_embedding_settings()
    if cfg is not None and cfg is not False and cfg.model:
        return cfg.model
    return "all-MiniLM-L6-v2"


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
