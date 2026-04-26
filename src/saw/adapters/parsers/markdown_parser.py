"""Markdown parser with YAML frontmatter and heading hierarchy.

Per D-06: Wiki pages use Markdown + YAML frontmatter.
Uses python-frontmatter for YAML extraction, markdown-it-py for AST.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import frontmatter
from markdown_it import MarkdownIt


@dataclass
class Heading:
    """A heading in the markdown document."""
    level: int
    text: str
    line: int


@dataclass
class MarkdownParseResult:
    """Result of parsing a markdown file."""
    title: str
    content: str
    frontmatter: dict
    headings: list[Heading]
    file_path: Path


class MarkdownParser:
    """Parse markdown files with frontmatter and heading hierarchy."""

    def __init__(self) -> None:
        self._md = MarkdownIt()

    def parse(self, file_path: Path) -> MarkdownParseResult:
        """Parse a markdown file.

        Args:
            file_path: Path to the markdown file.

        Returns:
            MarkdownParseResult with title, content, frontmatter, and headings.
        """
        # Load frontmatter and content
        post = frontmatter.load(str(file_path))
        frontmatter_data = post.metadata if hasattr(post, "metadata") else {}
        content = post.content

        # Extract title from frontmatter or first heading
        title = frontmatter_data.get("title", "")

        # Parse content for heading hierarchy
        headings = self._extract_headings(content)

        if not title and headings:
            title = headings[0].text

        return MarkdownParseResult(
            title=title,
            content=content,
            frontmatter=frontmatter_data,
            headings=headings,
            file_path=file_path,
        )

    def _extract_headings(self, content: str) -> list[Heading]:
        """Extract headings from markdown content."""
        headings: list[Heading] = []
        tokens = self._md.parse(content)

        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.type == "heading_open":
                # Level is from the tag (h1 -> level 1, h2 -> level 2, etc.)
                level = int(token.tag[1])
                # Next token should be inline with content
                if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                    inline_token = tokens[i + 1]
                    headings.append(Heading(
                        level=level,
                        text=inline_token.content,
                        line=inline_token.map[0] if inline_token.map else 0,
                    ))
                    i += 2  # Skip past heading_open and inline
                    continue
            i += 1

        return headings