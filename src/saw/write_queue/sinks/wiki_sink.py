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
        """Write (or delete) a wiki page from a WriteOp.

        Idempotent: overwrite is safe (Markdown files).

        - ``op == "delete"`` removes the page file.
        - ``op in ("write", "create")`` persists the page. Fields absent from
          the payload are preserved from the existing page on disk (so a
          content-only or properties-only update does not clobber the rest).
        """
        payload = op.payload
        operation = payload.get("op", "write")
        path = payload.get("path") or payload.get("slug") or f"concepts/{op.op_id}.md"

        if operation == "delete":
            self._repo.delete(path)
            return

        # Read the existing page so an update preserves fields the caller
        # did not supply (title, tags, confidence, freshness, entity_type,
        # properties, related, frontmatter).
        existing = self._repo.read(path)

        # The managed frontmatter keys are rebuilt from the explicit WikiPage
        # fields below. If we pass the existing frontmatter verbatim, the
        # repository's ``fm.update(page.frontmatter)`` step would overwrite
        # those freshly-set fields with the stale parsed values. So we strip
        # the managed keys and only carry through extra user-defined frontmatter.
        _MANAGED_FM_KEYS = {
            "type", "entity_type", "tags", "related",
            "confidence", "freshness", "record_type", "properties",
        }
        extra_fm: dict[str, object] = {}
        if existing is not None:
            extra_fm = {
                k: v for k, v in existing.frontmatter.items()
                if k not in _MANAGED_FM_KEYS
            }
        # Caller-supplied frontmatter (rare) merges over the preserved extras.
        extra_fm.update(payload.get("frontmatter", {}))

        page_type = existing.page_type if existing else PageType.SUMMARY
        if "page_type" in payload or "type" in payload:
            pt_str = str(payload.get("page_type", payload.get("type", "summary"))).upper()
            try:
                page_type = PageType[pt_str]
            except KeyError:
                page_type = PageType.SUMMARY

        confidence = existing.confidence if existing else ConfidenceLevel.UNVERIFIED
        if "confidence" in payload:
            conf_str = str(payload.get("confidence", "unverified")).upper()
            try:
                confidence = ConfidenceLevel[conf_str]
            except KeyError:
                confidence = ConfidenceLevel.UNVERIFIED

        freshness = existing.freshness if existing else FreshnessLevel.LEVEL_0
        if "freshness" in payload:
            try:
                freshness = FreshnessLevel(payload.get("freshness", 3))
            except ValueError:
                freshness = FreshnessLevel.LEVEL_0

        page = WikiPage(
            path=path,
            title=payload.get("title", existing.title if existing else op.op_id),
            page_type=page_type,
            entity_type=payload.get("entity_type", existing.entity_type if existing else "note"),
            tags=payload.get("tags", existing.tags if existing else []),
            related=payload.get("related", existing.related if existing else []),
            confidence=confidence,
            freshness=freshness,
            content=payload.get("content", existing.content if existing else ""),
            properties=payload.get("properties", existing.properties if existing else {}),
            frontmatter=extra_fm,
        )

        self._repo.write(page)

    def can_handle(self, sink_name: str) -> bool:
        return sink_name == "wiki"
