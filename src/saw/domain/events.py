"""Domain events for cross-engine communication."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from saw.domain.value_objects import ContradictionType, ResolutionStrategy


@dataclass(frozen=True)
class ContradictionFound:
    """Fired when a contradiction is detected between claims.

    Per D-06 to D-09: Two-phase detection with auto-resolution.
    """
    claim_a_uuid: str
    claim_b_uuid: str
    contradiction_type: ContradictionType
    resolution: ResolutionStrategy
    affected_pages: list[str]
    timestamp: datetime


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
