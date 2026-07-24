"""Code Wiki domain models.

Defines configuration and result types for repository-level
AI documentation generation (Code Wiki).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from saw.domain.utils import utcnow


@dataclass
class CodeWikiConfig:
    """Configuration for Code Wiki generation."""

    repo_path: Path
    target_path: str = ""  # Subdirectory for monorepo
    branch: str = "main"
    skip_if_exists: bool = False
    include_patterns: list[str] = field(
        default_factory=lambda: ["**/*.py", "**/*.ts", "**/*.tsx"]
    )
    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            "**/node_modules/**",
            "**/.git/**",
            "**/__pycache__/**",
            "**/dist/**",
            "**/build/**",
            "**/.venv/**",
        ]
    )
    depth: int = 3  # Directory depth for module grouping
    commit_hash: str = ""


@dataclass
class CodeWikiPage:
    """A generated Code Wiki page."""

    filename: str  # Relative to _wiki/code/ (e.g. "modules/auth.md")
    title: str
    content: str
    source_files: list[str] = field(default_factory=list)
    commit_hash: str = ""
    generated_at: datetime = field(default_factory=utcnow)


@dataclass
class CodeWikiStatus:
    """Status of Code Wiki for a repository."""

    exists: bool = False
    last_generated: Optional[datetime] = None
    last_commit: str = ""
    current_commit: str = ""
    pages_count: int = 0
    stale_pages: list[str] = field(default_factory=list)

    @property
    def is_stale(self) -> bool:
        return self.exists and self.last_commit != self.current_commit


@dataclass
class CodeWikiResult:
    """Result of a Code Wiki generation run."""

    pages_generated: list[str] = field(default_factory=list)
    pages_updated: list[str] = field(default_factory=list)
    pages_skipped: list[str] = field(default_factory=list)
    total_source_files: int = 0
    duration_seconds: float = 0.0
    commit_hash: str = ""

    @property
    def total_pages(self) -> int:
        return len(self.pages_generated) + len(self.pages_updated)
