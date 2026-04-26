"""Wiki page domain model."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from saw.domain.value_objects import ConfidenceLevel, FreshnessLevel, PageType


@dataclass
class WikiPage:
    """A wiki page with YAML frontmatter and Markdown content."""
    path: str
    title: str
    page_type: PageType = PageType.SUMMARY
    tags: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    freshness: FreshnessLevel = FreshnessLevel.LEVEL_0  # Freshest by default
    content: str = ""
    frontmatter: dict[str, Any] = field(default_factory=dict)


class WikiFrontmatter(BaseModel):
    """Pydantic model for wiki page YAML frontmatter validation."""
    type: str = "summary"
    tags: list[str] = []
    related: list[str] = []
    confidence: str = "unverified"
    freshness: int = 3
    record_type: str = "SUMMARY"
