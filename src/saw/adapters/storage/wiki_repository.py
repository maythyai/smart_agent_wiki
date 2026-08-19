"""Wiki repository - Markdown + YAML frontmatter page storage.

Per D-06/D-07: wiki/{concepts,entities,sources,collections}/ structure.
Pages use YAML frontmatter with type, tags, related, confidence, freshness.
"""
from __future__ import annotations

from pathlib import Path

import frontmatter
import yaml

from saw.domain.exceptions import StorageError
from saw.domain.value_objects import (
    ConfidenceLevel,
    FreshnessLevel,
    PageType,
)
from saw.domain.wiki import WikiPage


class WikiRepository:
    """Wiki page storage backed by Markdown + YAML frontmatter files.

    Implements the WikiRepository protocol.
    """

    def __init__(self, wiki_root: Path) -> None:
        self._root = Path(wiki_root)
        # Create namespace directories per D-07
        for subdir in ("concepts", "entities", "sources", "collections"):
            (self._root / subdir).mkdir(parents=True, exist_ok=True)

    def write(self, page: WikiPage) -> Path:
        """Write a wiki page as Markdown with YAML frontmatter.

        Overwrite is safe (Markdown files).
        """
        page_path = self._root / page.path
        page_path.parent.mkdir(parents=True, exist_ok=True)

        # Build frontmatter dict
        fm = {
            "type": page.page_type.name.lower(),
            "entity_type": page.entity_type,
            "tags": page.tags,
            "related": page.related,
            "confidence": page.confidence.name.lower(),
            "freshness": page.freshness.value,
            "record_type": page.page_type.name,
            "properties": page.properties,
        }
        # Merge any extra frontmatter from the page
        fm.update(page.frontmatter)

        try:
            # Serialize as YAML frontmatter + Markdown body
            fm_str = yaml.dump(fm, default_flow_style=False, allow_unicode=True)
            content = f"---\n{fm_str}---\n{page.content}"
            page_path.write_text(content, encoding="utf-8")
            return page_path
        except OSError as e:
            raise StorageError(f"Failed to write wiki page {page.path}: {e}") from e

    def read(self, path: str) -> WikiPage | None:
        """Parse a wiki page from file. Returns None if not found."""
        page_path = self._root / path
        if not page_path.is_file():
            return None

        try:
            post = frontmatter.load(str(page_path))
            fm = post.metadata

            page_type_name = fm.get("record_type", fm.get("type", "summary")).upper()
            try:
                page_type = PageType[page_type_name]
            except KeyError:
                page_type = PageType.SUMMARY

            conf_name = fm.get("confidence", "unverified").upper()
            try:
                confidence = ConfidenceLevel[conf_name]
            except KeyError:
                confidence = ConfidenceLevel.UNVERIFIED

            freshness_val = fm.get("freshness", 0)
            try:
                freshness = FreshnessLevel(freshness_val)
            except ValueError:
                freshness = FreshnessLevel.LEVEL_0

            return WikiPage(
                path=path,
                title=page_path.stem,
                page_type=page_type,
                entity_type=fm.get("entity_type", "note"),
                tags=fm.get("tags", []),
                related=fm.get("related", []),
                confidence=confidence,
                freshness=freshness,
                content=post.content,
                properties=fm.get("properties", {}),
                frontmatter=dict(fm),
            )
        except Exception as e:
            raise StorageError(f"Failed to read wiki page {path}: {e}") from e

    def list_pages(self) -> list[str]:
        """List all wiki page paths relative to wiki root."""
        pages: list[str] = []
        for md_file in self._root.rglob("*.md"):
            rel = md_file.relative_to(self._root)
            pages.append(str(rel))
        return sorted(pages)

    def count(self) -> int:
        """Count total wiki pages."""
        return sum(1 for _ in self._root.rglob("*.md"))

    def delete(self, path: str) -> bool:
        """Delete a wiki page file. Returns True if a file was removed."""
        page_path = self._root / path
        if not page_path.is_file():
            return False
        try:
            page_path.unlink()
            return True
        except OSError as e:
            raise StorageError(f"Failed to delete wiki page {path}: {e}") from e
