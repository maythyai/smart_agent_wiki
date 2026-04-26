"""Wiki sink - writes wiki pages as Markdown with YAML frontmatter.

Per Pitfall 7: idempotent (overwrite is safe for Markdown files).
"""
from __future__ import annotations

from saw.adapters.storage.wiki_repository import WikiRepository
from saw.domain.value_objects import ConfidenceLevel, FreshnessLevel, PageType
from saw.domain.wiki import WikiPage


class WikiSink:
    """Write Queue sink for wiki page storage."""

    def __init__(self, wiki_repo: WikiRepository) -> None:
        self._repo = wiki_repo

    @property
    def name(self) -> str:
        return "wiki"

    def write(self, op) -> None:
        """Write a wiki page from a WriteOp.

        Idempotent: overwrite is safe (Markdown files).
        """
        payload = op.payload

        # Parse page type
        pt_str = payload.get("page_type", "summary").upper()
        try:
            page_type = PageType[pt_str]
        except KeyError:
            page_type = PageType.SUMMARY

        # Parse confidence
        conf_str = payload.get("confidence", "unverified").upper()
        try:
            confidence = ConfidenceLevel[conf_str]
        except KeyError:
            confidence = ConfidenceLevel.UNVERIFIED

        # Parse freshness
        freshness_val = payload.get("freshness", 3)
        try:
            freshness = FreshnessLevel(freshness_val)
        except ValueError:
            freshness = FreshnessLevel.FRESH

        page = WikiPage(
            path=payload.get("path", f"concepts/{op.op_id}.md"),
            title=payload.get("title", op.op_id),
            page_type=page_type,
            tags=payload.get("tags", []),
            related=payload.get("related", []),
            confidence=confidence,
            freshness=freshness,
            content=payload.get("content", ""),
            frontmatter=payload.get("frontmatter", {}),
        )

        self._repo.write(page)

    def can_handle(self, sink_name: str) -> bool:
        return sink_name == "wiki"
