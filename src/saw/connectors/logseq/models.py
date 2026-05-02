"""Pydantic models for Logseq connector.

Plan 13-01 Task 1: Logseq models for configuration and parsing.
Per LOGS-01: User can configure Logseq graph path.
Per LOGS-02: Block parsing model.
Per LOGS-03: Property drawer extraction.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

from pydantic import BaseModel, field_validator


class LogseqConfig(BaseModel):
    """Configuration for Logseq graph sync.

    Per LOGS-01: User can configure Logseq graph path.

    Attributes:
        graph_path: Path to Logseq graph directory (must exist).
        sync_enabled: Whether sync is enabled.
        watch_enabled: Whether real-time file watching is enabled.
    """

    graph_path: Path
    sync_enabled: bool = True
    watch_enabled: bool = True

    @field_validator("graph_path")
    @classmethod
    def validate_graph_path(cls, v: Path) -> Path:
        """Validate that graph_path exists and is a directory.

        Per LOGS-01: User can configure Logseq graph directory path.
        Per T-13-01: Validate file paths are within graph_path.

        Args:
            v: Path to validate.

        Returns:
            Validated path.

        Raises:
            ValueError: If path doesn't exist or is not a directory.
        """
        if not v.exists():
            raise ValueError(f"Graph path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Graph path is not a directory: {v}")
        return v


@dataclass
class BlockNode:
    """Represents a parsed bullet point/block from Logseq.

    Per LOGS-02: System parses Markdown files and extracts blocks as Claims.
    Per LOGS-10: System preserves Logseq wikilink syntax during sync.

    Attributes:
        id: Unique block identifier (file_id-block_index).
        content: Block content text (wikilinks preserved).
        level: Nesting level (0 = top level).
        parent_id: Parent block ID for nested blocks.
        properties: Block-level properties (:: syntax).
    """

    id: str
    content: str
    level: int
    parent_id: Optional[str] = None
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class PropertyDrawer:
    """Extracted properties from Logseq frontmatter.

    Per LOGS-03: System handles property drawers as Claim metadata.

    Attributes:
        title: Page title from frontmatter.
        id: Page UUID if present.
        tags: List of tags (parsed from [[tag]] format).
        confidence: Confidence tier if specified.
        created_at: Creation timestamp if present.
        custom: Additional custom properties.
    """

    title: str
    id: Optional[str] = None
    tags: list[list[str]] = field(default_factory=list)
    confidence: Optional[str] = None
    created_at: Optional[datetime] = None
    custom: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedPage:
    """A fully parsed Logseq Markdown page.

    Per LOGS-09: System maps Logseq namespaces to SAW Wiki page hierarchy.

    Attributes:
        file_path: Path to the source file.
        title: Page title.
        namespace: Namespace derived from file path.
        blocks: List of parsed blocks.
        properties: Property drawer from frontmatter.
    """

    file_path: Path
    title: str
    namespace: str
    blocks: list[BlockNode]
    properties: PropertyDrawer
