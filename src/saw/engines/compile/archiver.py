"""Query archiver.

Archives query results as Wiki pages (type=archive), turning Q&A
knowledge into persistent, searchable wiki entries.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from saw.domain.wiki_compile import (
    CompileLogEntry,
    WikiCompilePage,
    WikiConfidence,
    WikiPageMetadata,
    WikiPageType,
    WikiSource,
)
from saw.domain.utils import utcnow


class QueryArchiver:
    """Archives query answers as wiki pages.

    Archive pages are point-in-time snapshots that do NOT receive
    cascade updates. They are the only page type allowed to reference
    other wiki pages in their sources.
    """

    def __init__(self, wiki_root: Path) -> None:
        self._wiki_root = wiki_root
        self._archive_dir = wiki_root / "archive"

    async def archive(
        self,
        query: str,
        answer: str,
        referenced_pages: list[str],
        confidence: str = "medium",
    ) -> WikiCompilePage:
        """Archive a query result as a wiki page."""
        self._archive_dir.mkdir(parents=True, exist_ok=True)

        slug = self._slugify(query[:60])
        filename = f"archive/{slug}.md"
        title = self._make_title(query)

        # Build sources from referenced wiki pages (archive exception)
        sources = [
            WikiSource(page_id=f"wiki/{p}", title=p.removesuffix(".md").split("/")[-1])
            for p in referenced_pages
        ]

        try:
            conf = WikiConfidence(confidence)
        except ValueError:
            conf = WikiConfidence.MEDIUM

        metadata = WikiPageMetadata(
            type=WikiPageType.ARCHIVE,
            confidence=conf,
            sources=sources,
            topic="archive",
        )

        # Render archive page
        now = utcnow().strftime("%Y-%m-%d")
        content = f"""# {title}

> Archived from query on {now}. This is a point-in-time snapshot
> and will NOT receive cascade updates.

## Overview

{query}

## Findings

{answer}

## See Also

"""
        for page in referenced_pages:
            link = page.removesuffix(".md")
            content += f"- [[{link}]]\n"

        page = WikiCompilePage(
            filename=filename,
            title=title,
            content=content,
            metadata=metadata,
        )

        # Write page
        self._write_archive_page(page)

        # Update index
        self._update_index(page)

        # Append log
        self._append_log(page, query)

        return page

    async def suggest_archive(
        self, query: str, answer: str, referenced_pages: list[str]
    ) -> bool:
        """Determine if a query result is worth archiving.

        Suggests archive when at least 2 of these conditions are met:
        - Answer synthesizes 3+ wiki pages
        - Answer contains inferences not explicitly in source pages
        - Query has reuse value (not a one-time fact lookup)
        - Answer reveals new cross-page connections
        """
        score = 0
        if len(referenced_pages) >= 3:
            score += 1
        if len(answer) > 500:
            score += 1
        # Heuristic: questions with "how", "why", "compare" have reuse value
        lower_query = query.lower()
        if any(w in lower_query for w in ("how", "why", "compare", "difference", "best")):
            score += 1
        if len(referenced_pages) >= 2 and "relationship" in answer.lower():
            score += 1
        return score >= 2

    def list_archives(self) -> list[str]:
        """List all archived pages."""
        if not self._archive_dir.exists():
            return []
        return sorted(
            str(p.relative_to(self._wiki_root))
            for p in self._archive_dir.glob("*.md")
        )

    # ─── Private helpers ───────────────────────────────────────────────

    def _slugify(self, text: str) -> str:
        slug = text.lower().strip()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[\s_]+", "-", slug)
        return slug.strip("-")[:50]

    def _make_title(self, query: str) -> str:
        """Create a title from the query."""
        # Remove question marks and truncate
        title = query.replace("?", "").strip()
        if len(title) > 80:
            title = title[:77] + "..."
        return title

    def _write_archive_page(self, page: WikiCompilePage) -> None:
        """Write archive page with metadata."""
        page_path = self._wiki_root / page.filename
        page_path.parent.mkdir(parents=True, exist_ok=True)

        output = page.content.rstrip() + "\n\n"
        output += "<!-- metadata:\n"
        output += f"type: {page.metadata.type.value}\n"
        output += f"confidence: {page.metadata.confidence.value}\n"
        output += "sources:\n"
        for src in page.metadata.sources:
            output += f'  - pageId: "{src.page_id}"\n'
            output += f'    title: "{src.title}"\n'
        output += f"created: {page.metadata.created.isoformat()}\n"
        output += "-->\n"

        page_path.write_text(output, encoding="utf-8")

    def _update_index(self, page: WikiCompilePage) -> None:
        """Add archived page to index.md with [Archived] prefix."""
        index_path = self._wiki_root / "index.md"
        if not index_path.exists():
            return
        content = index_path.read_text(encoding="utf-8")

        # Ensure Archive section exists
        if "## Archive" not in content:
            content += "\n## Archive\n\n| Page | Summary | Updated |\n|------|---------|---------|\n"

        # Add entry
        slug = page.filename.removesuffix(".md")
        date_str = utcnow().strftime("%Y-%m-%d")
        source_count = len(page.metadata.sources)
        row = f"| [Archived] [[{slug}]] | archive ({source_count} sources) | {date_str} |\n"

        # Insert after Archive table header
        content = content.replace(
            "|------|---------|---------|\n",
            f"|------|---------|---------|\n{row}",
            1,
        ) if "## Archive" in content and row not in content else content

        index_path.write_text(content, encoding="utf-8")

    def _append_log(self, page: WikiCompilePage, query: str) -> None:
        """Append archive action to log.md."""
        log_path = self._wiki_root / "log.md"
        if not log_path.exists():
            return
        entry = CompileLogEntry(
            timestamp=utcnow(),
            action="archive",
            pages_affected=[page.filename],
            summary=f"Archived query: {query[:80]}",
        )
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n" + entry.to_markdown())
