"""Claim domain model."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

from saw.domain.value_objects import ConfidenceLevel, SourceMark


@dataclass
class Claim:
    """A structured assertion extracted from a source document.

    Every claim traces back to its Vault source via source_uuid.
    """
    uuid: str
    content: str
    source_uuid: str
    content_hash: str
    confidence: ConfidenceLevel = ConfidenceLevel.UNVERIFIED
    source_mark: SourceMark = SourceMark.EXTRACTED
    page_number: int | None = None
    line_number: int | None = None
    timestamp: str | None = None
    tags: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    # Phase 4: Media Ingestion — timestamp for video/audio source
    media_timestamp: tuple[float, float] | None = None  # (start_seconds, end_seconds)
    media_vault_id: str | None = None  # Reference to media vault entry
    # F-CONN-04: connector provenance for sync conflict detection.
    source_platform: str | None = None
    source_id: str | None = None
    # T-F-P-4: workspace isolation (ADR-005). 'default' for single-wiki
    # local-first backward compat.
    workspace_id: str = "default"

    @classmethod
    def compute_hash(cls, content: str) -> str:
        """Compute SHA-256 hash of claim content for deduplication."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
