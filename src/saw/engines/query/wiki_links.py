"""Wiki link parser and resolver for bidirectional linking.

Parses [[wiki-links]] from content and resolves them to page slugs.
Supports Obsidian-style syntax: [[page]], [[page|alias]], [[page#section]]
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class WikiLink:
    """Parsed wiki link."""
    target: str  # Target page slug
    alias: str | None = None  # Display text (if different from target)
    section: str | None = None  # Section anchor (if specified)
    raw: str = ""  # Original raw syntax


# Pattern matches: [[target]], [[target|alias]], [[target#section]], [[target#section|alias]]
WIKI_LINK_PATTERN = re.compile(
    r'\[\['
    r'(?P<target>[^|#\]]+)'
    r'(?:#(?P<section>[^|\]]+))?'
    r'(?:\|(?P<alias>[^\]]+))?'
    r'\]\]'
)


def parse_wiki_links(content: str) -> list[WikiLink]:
    """Extract all [[wiki-links]] from content.

    Args:
        content: Markdown content to parse.

    Returns:
        List of WikiLink objects found in content.

    Example:
        >>> parse_wiki_links("See [[Python]] and [[Rust|the Rust lang]]")
        [WikiLink(target='python', alias=None), WikiLink(target='rust', alias='the Rust lang')]
    """
    links: list[WikiLink] = []
    for match in WIKI_LINK_PATTERN.finditer(content):
        target = match.group("target").strip()
        alias = match.group("alias")
        section = match.group("section")

        # Normalize target to slug format
        slug = slugify(target)

        links.append(WikiLink(
            target=slug,
            alias=alias.strip() if alias else None,
            section=section.strip() if section else None,
            raw=match.group(0),
        ))

    return links


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug.

    Args:
        text: Input text.

    Returns:
        Lowercase slug with spaces replaced by hyphens.
    """
    # Remove special chars, keep alphanumeric and hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    return slug


def extract_unique_targets(content: str) -> set[str]:
    """Get unique target slugs from content.

    Args:
        content: Markdown content.

    Returns:
        Set of unique target slugs.
    """
    links = parse_wiki_links(content)
    return {link.target for link in links}
