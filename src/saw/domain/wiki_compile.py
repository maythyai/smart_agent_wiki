"""Wiki compile layer domain models.

Defines the structured Wiki output layer that sits above the immutable Vault
and Claims store. The compile layer produces human/agent-readable Markdown
organized by topic with structured metadata and full source traceability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from saw.domain.utils import utcnow


class WikiPageType(str, Enum):
    """Wiki page types (8 allowed values)."""

    CONCEPT = "concept"
    FAQ = "faq"
    HOWTO = "howto"
    REFERENCE = "reference"
    COMPARISON = "comparison"
    ARCHIVE = "archive"
    SOURCE_SUMMARY = "source-summary"
    ENTITY = "entity"


class WikiConfidence(str, Enum):
    """Confidence level for compiled wiki pages."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class WikiSource:
    """Traceable source reference for a wiki page.

    Sources must point to raw documents in the Vault (never to other wiki
    pages), except for type=archive which may reference wiki pages.
    """

    page_id: str
    title: str  # Human-readable title; must NOT be a pageId
    sections: tuple[str, ...] = ()
    repo_id: Optional[str] = None  # Required for cross-repo references

    def __post_init__(self) -> None:
        if not self.title or self.title == self.page_id:
            raise ValueError(
                f"WikiSource.title must be human-readable, got: {self.title!r}"
            )


@dataclass
class WikiPageMetadata:
    """Structured metadata for a compiled wiki page."""

    type: WikiPageType
    confidence: WikiConfidence
    sources: list[WikiSource] = field(default_factory=list)
    see_also: list[str] = field(default_factory=list)
    topic: str = ""
    created: datetime = field(default_factory=utcnow)
    updated: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "confidence": self.confidence.value,
            "sources": [
                {
                    "pageId": s.page_id,
                    "title": s.title,
                    "sections": list(s.sections),
                    **({"repoId": s.repo_id} if s.repo_id else {}),
                }
                for s in self.sources
            ],
            "seeAlso": self.see_also,
            "topic": self.topic,
            "created": self.created.isoformat(),
            "updated": self.updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> WikiPageMetadata:
        sources = [
            WikiSource(
                page_id=s["pageId"],
                title=s["title"],
                sections=tuple(s.get("sections", [])),
                repo_id=s.get("repoId"),
            )
            for s in data.get("sources", [])
        ]
        return cls(
            type=WikiPageType(data["type"]),
            confidence=WikiConfidence(data["confidence"]),
            sources=sources,
            see_also=data.get("seeAlso", []),
            topic=data.get("topic", ""),
            created=datetime.fromisoformat(data["created"]) if "created" in data else utcnow(),
            updated=datetime.fromisoformat(data["updated"]) if "updated" in data else utcnow(),
        )


@dataclass
class WikiCompilePage:
    """A page in the wiki compile layer."""

    filename: str  # Relative to _wiki/ (e.g. "concepts/event-sourcing.md")
    title: str
    content: str  # Markdown body
    metadata: WikiPageMetadata
    is_index: bool = False
    is_log: bool = False

    @property
    def topic(self) -> str:
        """Extract topic from filename (first path component)."""
        parts = self.filename.split("/")
        return parts[0] if len(parts) > 1 else ""


@dataclass
class WikiIndexEntry:
    """A single entry in the wiki index."""

    filename: str
    title: str
    summary: str  # One-line summary including source count
    updated: datetime
    is_archived: bool = False

    def to_markdown_row(self) -> str:
        prefix = "[Archived] " if self.is_archived else ""
        link = f"[[{self.filename.removesuffix('.md')}]]"
        date_str = self.updated.strftime("%Y-%m-%d")
        return f"| {prefix}{link} | {self.summary} | {date_str} |"


@dataclass
class WikiIndex:
    """The living index (index.md) structure."""

    topics: dict[str, list[WikiIndexEntry]] = field(default_factory=dict)
    total_pages: int = 0
    total_sources: int = 0
    contradictions: int = 0
    last_updated: datetime = field(default_factory=utcnow)

    def add_entry(self, topic: str, entry: WikiIndexEntry) -> None:
        if topic not in self.topics:
            self.topics[topic] = []
        # Replace existing entry with same filename
        self.topics[topic] = [
            e for e in self.topics[topic] if e.filename != entry.filename
        ]
        self.topics[topic].append(entry)
        self.total_pages = sum(len(v) for v in self.topics.values())

    def remove_entry(self, filename: str) -> bool:
        for topic, entries in self.topics.items():
            original_len = len(entries)
            self.topics[topic] = [e for e in entries if e.filename != filename]
            if len(self.topics[topic]) < original_len:
                self.total_pages = sum(len(v) for v in self.topics.values())
                return True
        return False


@dataclass
class CompileLogEntry:
    """An entry in the append-only compile log (log.md)."""

    timestamp: datetime
    action: str  # ingest | lint | organize | archive | update | compile
    pages_affected: list[str] = field(default_factory=list)
    summary: str = ""
    sources_processed: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    def to_markdown(self) -> str:
        ts = self.timestamp.strftime("%Y-%m-%dT%H:%M:%S+08:00")
        lines = [f"## {ts} — {self.action.upper()}", ""]
        lines.append(f"- Action: {self.action}")
        if self.sources_processed:
            srcs = ", ".join(f"`{s}`" for s in self.sources_processed)
            lines.append(f"- Sources processed: {srcs}")
        if self.pages_affected:
            lines.append(f"- Pages affected: {len(self.pages_affected)}")
            for p in self.pages_affected[:10]:
                lines.append(f"  - `{p}`")
        if self.summary:
            lines.append(f"- Summary: {self.summary}")
        if self.duration_seconds > 0:
            lines.append(f"- Duration: {self.duration_seconds:.1f}s")
        lines.append("")
        return "\n".join(lines)


@dataclass
class CompileResult:
    """Result of a compile operation."""

    pages_created: list[str] = field(default_factory=list)
    pages_updated: list[str] = field(default_factory=list)
    pages_unchanged: list[str] = field(default_factory=list)
    contradictions_found: list[str] = field(default_factory=list)
    log_entry: Optional[CompileLogEntry] = None
    duration_seconds: float = 0.0

    @property
    def total_affected(self) -> int:
        return len(self.pages_created) + len(self.pages_updated)
