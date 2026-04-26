"""Trend Senser - gap detection and synthesis suggestions.

Per D-21: Monitor knowledge growth patterns, detect gaps, suggest synthesis.
Identifies topics with high query count but low coverage.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from saw.domain.protocols import ClaimsRepository, WikiRepository


@dataclass
class KnowledgeGap:
    """A detected knowledge gap.

    High query count + low coverage = gap that needs filling.

    Attributes:
        topic: The topic area with the gap
        query_count: How often users query this topic
        coverage: Coverage ratio (0.0 to 1.0)
        suggested_sources: Potential sources to ingest
    """
    topic: str
    query_count: int
    coverage: float
    suggested_sources: list[str]


class TrendSenser:
    """Monitors knowledge growth patterns and detects gaps (per D-21).

    Identifies areas where users frequently query but have little coverage.
    Suggests synthesis pages to fill gaps.
    """

    # Threshold for gap detection
    HIGH_QUERY_THRESHOLD = 20  # queries
    LOW_COVERAGE_THRESHOLD = 0.5  # coverage ratio

    def __init__(
        self,
        claims_repo: ClaimsRepository,
        wiki_repo: WikiRepository,
    ) -> None:
        self._claims = claims_repo
        self._wiki = wiki_repo

    def detect_gaps(self) -> list[KnowledgeGap]:
        """Identify knowledge gaps (per D-21 gap detection).

        Analyzes query patterns for high-query, low-coverage topics.

        Returns:
            List of detected knowledge gaps.
        """
        gaps: list[KnowledgeGap] = []

        # In production, this would analyze query logs
        # For now, we return a placeholder implementation

        # Would iterate through topics and check:
        # 1. Query count from logs
        # 2. Coverage from claims search
        # 3. If query_count > threshold AND coverage < threshold -> gap

        return gaps

    def suggest_synthesis(self, gaps: list[KnowledgeGap]) -> list[str]:
        """Recommend synthesis pages for gap areas (per D-21).

        Args:
            gaps: List of detected knowledge gaps.

        Returns:
            List of suggested page paths to create.
        """
        suggestions: list[str] = []

        for gap in gaps:
            # Suggest a wiki page name based on the topic
            page_name = gap.topic.lower().replace(" ", "-")

            # For high-priority gaps (high query, very low coverage)
            if gap.query_count > self.HIGH_QUERY_THRESHOLD * 2 and gap.coverage < self.LOW_COVERAGE_THRESHOLD / 2:
                suggestions.append(f"concepts/{page_name}.md")

            # Also suggest ingesting suggested sources
            if gap.suggested_sources:
                suggestions.append(f"sources/{page_name}.md")

        return suggestions

    def get_growth_patterns(self) -> dict[str, int]:
        """Get topic growth over time.

        Returns:
            Dict mapping topic to growth count.
        """
        # In production, this would analyze claims over time
        # For now, return placeholder
        return {}

    def analyze_coverage(self, topic: str) -> float:
        """Analyze coverage ratio for a topic.

        Args:
            topic: Topic to analyze.

        Returns:
            Coverage ratio (0.0 to 1.0).
        """
        # Search for claims related to topic
        claims = self._claims.search(topic, limit=100)

        # Get pages related to topic
        pages = self._wiki.list_pages()

        # Simple coverage heuristic: number of matching claims / expected
        if len(claims) >= 10:
            return 0.8  # Good coverage
        elif len(claims) >= 5:
            return 0.5  # Moderate coverage
        elif len(claims) >= 1:
            return 0.2  # Low coverage
        else:
            return 0.0  # No coverage