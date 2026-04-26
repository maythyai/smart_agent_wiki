"""Domain events for cross-engine communication."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ClaimsReady:
    """Fired when a batch of claims has been extracted and stored."""
    claim_ids: list[str]
    session_id: str


@dataclass(frozen=True)
class WriteFailed:
    """Fired when a write operation fails after retries."""
    op_id: str
    sink_name: str
    error: str


@dataclass(frozen=True)
class IngestCompleted:
    """Fired when a full ingestion session completes."""
    source: str
    claim_count: int
    session_id: str
