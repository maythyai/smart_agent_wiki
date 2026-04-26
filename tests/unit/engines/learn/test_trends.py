"""Tests for TrendSenser - gap detection and synthesis suggestions.

Per D-21: Knowledge gap detection from query patterns.
"""
from __future__ import annotations

import unittest
from unittest.mock import Mock

from saw.engines.learn.trends import TrendSenser, KnowledgeGap


class TestTrendSenser(unittest.TestCase):
    """Test cases for trend sensing and gap detection."""

    def test_detect_gaps_returns_list(self) -> None:
        """Test 2: TrendSenser.detect_gaps() identifies knowledge gaps (per D-21)."""
        mock_claims_repo = Mock()
        mock_wiki_repo = Mock()

        mock_claims_repo.search.return_value = []  # No claims for this topic
        mock_wiki_repo.list_pages.return_value = []

        senser = TrendSenser(mock_claims_repo, mock_wiki_repo)

        # detect_gaps would analyze query logs
        gaps = senser.detect_gaps()

        self.assertIsInstance(gaps, list)

    def test_suggest_synthesis_returns_pages(self) -> None:
        """Test 3: TrendSenser.suggest_synthesis() recommends synthesis pages."""
        mock_claims_repo = Mock()
        mock_wiki_repo = Mock()

        senser = TrendSenser(mock_claims_repo, mock_wiki_repo)

        gaps = [
            KnowledgeGap(
                topic="transformer architecture",
                query_count=50,
                coverage=0.3,
                suggested_sources=["attention-paper.pdf"],
            ),
        ]

        suggestions = senser.suggest_synthesis(gaps)

        self.assertIsInstance(suggestions, list)
        # Should suggest a page for the gap
        self.assertTrue(len(suggestions) >= 1)

    def test_get_growth_patterns(self) -> None:
        """Test getting topic growth patterns."""
        mock_claims_repo = Mock()
        mock_wiki_repo = Mock()

        senser = TrendSenser(mock_claims_repo, mock_wiki_repo)

        patterns = senser.get_growth_patterns()

        self.assertIsInstance(patterns, dict)


class TestKnowledgeGap(unittest.TestCase):
    """Test cases for KnowledgeGap dataclass."""

    def test_gap_creation(self) -> None:
        """Test creating a knowledge gap."""
        gap = KnowledgeGap(
            topic="machine learning basics",
            query_count=100,
            coverage=0.2,
            suggested_sources=["ml-book.pdf", "ml-course.pdf"],
        )

        self.assertEqual(gap.topic, "machine learning basics")
        self.assertEqual(gap.query_count, 100)
        self.assertEqual(gap.coverage, 0.2)
        self.assertEqual(len(gap.suggested_sources), 2)


if __name__ == "__main__":
    unittest.main()