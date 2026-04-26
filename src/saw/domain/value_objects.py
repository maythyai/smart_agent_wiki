"""Domain value objects - enums and dataclass references.

Pure Python, zero external I/O dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class ConfidenceLevel(IntEnum):
    """4-tier confidence system (per D-06).

    Higher value = higher confidence.
    """
    UNVERIFIED = 1
    SINGLE_SOURCE = 2
    CROSS_VALIDATED = 3
    HUMAN_VERIFIED = 4


class SourceMark(IntEnum):
    """Source mark for claim provenance."""
    EXTRACTED = 1   # Directly extracted from source
    INFERRED = 2    # Inferred by LLM or reasoning
    AMBIGUOUS = 3   # Uncertain provenance


class FreshnessLevel(IntEnum):
    """9-level freshness system (1=freshest, 9=stalest).

    Constants only; calculation logic comes in Phase 2.
    """
    FRESHEST = 1
    VERY_FRESH = 2
    FRESH = 3
    RECENT = 4
    MODERATE = 5
    AGING = 6
    STALE = 7
    VERY_STALE = 8
    STALEST = 9


class PageType(IntEnum):
    """Wiki page record types (per D-06)."""
    SUMMARY = 1
    META = 2
    SOURCE = 3
    ALIAS = 4
    COLLECTION = 5


class CapabilityTier(IntEnum):
    """Three-tier degradation (per D-22).

    Higher value = more capabilities available.
    """
    OFFLINE = 1      # BM25+TF-IDF, zero LLM
    LIGHTWEIGHT = 2  # LLM + BM25 only
    FULL = 3         # LLM + embeddings + vector


class WriteOpStatus(IntEnum):
    """Write operation lifecycle states (per D-04)."""
    PENDING = 1
    PROCESSING = 2
    DONE = 3
    FAILED = 4


@dataclass(frozen=True)
class ClaimRef:
    """Reference to a claim within the system."""
    uuid: str
    source_uuid: str
    page_location: str | None = None


@dataclass(frozen=True)
class WikiPageRef:
    """Reference to a wiki page."""
    path: str
    title: str
    page_type: PageType
