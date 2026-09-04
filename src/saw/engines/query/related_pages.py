"""Related Pages Calculator - 相关页面计算.

Computes related pages using 3 signals:
1. Shared tags (Jaccard similarity, weight 2.0)
2. Shared links (Jaccard similarity, weight 3.0)
3. Type affinity (same type, weight 1.0)
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from saw.engines.query.wiki_links import extract_unique_targets


@dataclass
class RelatedPage:
    """A related page with score and reasons."""
    slug: str
    title: str
    score: float
    shared_tags: list[str]
    shared_links: list[str]
    same_type: bool
    embedding_sim: float | None = None


def compute_related_pages(
    slug: str,
    wiki_repo,
    top_k: int = 8,
    conn: "sqlite3.Connection | None" = None,
    workspace_id: str = "default",
) -> list[dict]:
    """Compute related pages for a given page.

    Args:
        slug: The source page slug.
        wiki_repo: Wiki repository to read pages from.
        top_k: Maximum number of results.
        conn: Optional SQLite connection for embedding similarity
            (Signal 4, tier=FULL only). When None, the embedding signal
            is skipped — behavior is identical to the 3-signal v1.8.0 path.
        workspace_id: Workspace scope for embedding queries (ADR-007).

    Returns:
        List of dicts with slug, title, score, and reason.
    """
    if wiki_repo is None:
        return []

    source_page = wiki_repo.read(slug)
    if source_page is None:
        return []

    # Extract source page signals
    source_tags = set(t.lower() for t in source_page.tags)
    source_links = extract_unique_targets(source_page.content)
    source_type = str(source_page.page_type.value) if hasattr(source_page.page_type, "value") else "summary"

    # Signal 4 prep: load source page embedding vector if available
    src_embedding: list[float] | None = None
    if conn is not None:
        from saw.adapters.embeddings import embeddings_available

        if embeddings_available():
            import struct

            src_row = conn.execute(
                "SELECT vector, dim FROM embedding_store "
                "WHERE doc_id = ? AND workspace_id = ?",
                (slug, workspace_id),
            ).fetchone()
            if src_row:
                src_embedding = list(struct.unpack(f"<{src_row[1]}f", src_row[0]))

    results: list[RelatedPage] = []

    for page_slug in wiki_repo.list_pages():
        if page_slug == slug:
            continue

        page = wiki_repo.read(page_slug)
        if page is None:
            continue

        page_tags = set(t.lower() for t in page.tags)
        page_links = extract_unique_targets(page.content)
        page_type = str(page.page_type.value) if hasattr(page.page_type, "value") else "summary"

        # Signal 1: Shared tags (Jaccard similarity, weight 2.0)
        shared_tags = source_tags & page_tags
        tag_score = 0.0
        if source_tags and page_tags:
            union = source_tags | page_tags
            tag_score = (len(shared_tags) / len(union)) * 2.0

        # Signal 2: Shared links (Jaccard similarity, weight 3.0)
        shared_links = source_links & page_links
        link_score = 0.0
        if source_links and page_links:
            union = source_links | page_links
            link_score = (len(shared_links) / len(union)) * 3.0

        # Signal 3: Type affinity (weight 1.0)
        same_type = source_type == page_type
        type_score = 1.0 if same_type else 0.0

        # Signal 4: Embedding similarity (weight 2.5, tier=FULL only)
        embedding_sim: float | None = None
        embedding_score = 0.0
        if conn is not None and src_embedding is not None:
            from saw.adapters.embeddings import embeddings_available, cosine_similarity

            if embeddings_available():
                import struct

                tgt_row = conn.execute(
                    "SELECT vector, dim FROM embedding_store "
                    "WHERE doc_id = ? AND workspace_id = ?",
                    (page_slug, workspace_id),
                ).fetchone()
                if tgt_row:
                    tgt_vec = list(struct.unpack(f"<{tgt_row[1]}f", tgt_row[0]))
                    sim = cosine_similarity(src_embedding, tgt_vec)
                    embedding_sim = sim
                    embedding_score = sim * 2.5  # weight 2.5

        total_score = tag_score + link_score + type_score + embedding_score

        if total_score > 0:
            results.append(RelatedPage(
                slug=page_slug,
                title=page.title,
                score=round(total_score, 3),
                shared_tags=list(shared_tags),
                shared_links=list(shared_links),
                same_type=same_type,
                embedding_sim=embedding_sim,
            ))

    # Sort by score descending
    results.sort(key=lambda r: -r.score)

    return [
        {
            "slug": r.slug,
            "title": r.title,
            "score": r.score,
            "reasons": _build_reasons(r),
        }
        for r in results[:top_k]
    ]


def _build_reasons(r: RelatedPage) -> list[str]:
    """Build human-readable reason strings."""
    reasons = []
    if r.shared_tags:
        reasons.append(f"shared tags: {', '.join(sorted(r.shared_tags)[:3])}")
    if r.shared_links:
        reasons.append(f"shared links: {', '.join(sorted(r.shared_links)[:3])}")
    if r.same_type:
        reasons.append("same type")
    if r.embedding_sim is not None and r.embedding_sim > 0.3:
        reasons.append(f"semantic similarity: {r.embedding_sim:.2f}")
    return reasons
