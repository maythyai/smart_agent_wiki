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
    """9-level freshness system (0=freshest, 8=stalest).

    Per D-10 and D-11:
    - Levels 0-2: Green (fresh)
    - Levels 3-5: Yellow (recent)
    - Levels 6-7: Orange (aging)
    - Level 8: Red (stale)
    """
    LEVEL_0 = 0  # Just created
    LEVEL_1 = 1  # 1 day old
    LEVEL_2 = 2  # 3 days old (green boundary)
    LEVEL_3 = 3  # 1 week old (yellow boundary)
    LEVEL_4 = 4  # 2 weeks old
    LEVEL_5 = 5  # 1 month old (yellow boundary)
    LEVEL_6 = 6  # 3 months old (orange boundary)
    LEVEL_7 = 7  # 6 months old
    LEVEL_8 = 8  # Over 6 months (red)


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


class ContradictionType(IntEnum):
    """Contradiction classification types (per D-08).

    Used by ContradictionDetector to classify detected conflicts.
    """
    TEMPORAL = 1  # New data supersedes old (time-based)
    OPINION = 2   # Different perspectives (subjective)
    FACTUAL = 3   # Hard conflict (objective)


class ResolutionStrategy(IntEnum):
    """Resolution strategies for contradictions (per D-09).

    Applied automatically based on contradiction type.
    """
    SUPERSEDED = 1  # Temporal: new claim replaces old
    DISPUTED = 2    # Opinion: both preserved with flag
    HISTORICAL = 3  # Factual: both preserved for review


@dataclass(frozen=True)
class WikiPageRef:
    """Reference to a wiki page."""
    path: str
    title: str
    page_type: PageType
