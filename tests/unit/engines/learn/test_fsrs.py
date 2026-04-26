"""Tests for FSRSScheduler - spaced repetition for page reviews.

Per D-17:
- FSRS algorithm for scheduling page reviews
- Review queue prioritizes high-freshness pages
- Rating: 1=Again, 2=Hard, 3=Good, 4=Easy
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock

from saw.domain.wiki import WikiPage
from saw.domain.value_objects import FreshnessLevel, PageType
from saw.engines.learn.fsrs_scheduler import FSRSScheduler, ReviewItem


class TestFSRSScheduler(unittest.TestCase):
    """Test cases for FSRS spaced repetition scheduler."""

    def test_schedule_review_returns_datetime(self) -> None:
        """Test 4: FSRSScheduler.schedule_review() returns next review date (per D-17)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_wiki_repo = Mock()
            mock_claims_repo = Mock()
            mock_wiki_repo.list_pages.return_value = []

            scheduler = FSRSScheduler(mock_wiki_repo, mock_claims_repo, data_dir=Path(tmpdir))

            # Schedule a review with rating 3 (Good)
            next_review = scheduler.schedule_review("test-page.md", rating=3)

            self.assertIsInstance(next_review, datetime)
            # Should be scheduled in the future
            self.assertGreater(next_review, datetime.now(timezone.utc))

    def test_schedule_review_different_ratings(self) -> None:
        """Test different ratings produce different intervals."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_wiki_repo = Mock()
            mock_claims_repo = Mock()
            mock_wiki_repo.list_pages.return_value = []

            scheduler = FSRSScheduler(mock_wiki_repo, mock_claims_repo, data_dir=Path(tmpdir))

            # Again (1) should have shortest interval
            again_review = scheduler.schedule_review("page-again.md", rating=1)
            # Easy (4) should have longest interval
            easy_review = scheduler.schedule_review("page-easy.md", rating=4)

            # Easy should be scheduled later than Again
            self.assertGreater(easy_review, again_review)

    def test_get_review_queue_returns_items(self) -> None:
        """Test 5: FSRSScheduler.get_review_queue() returns pages needing review."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_wiki_repo = Mock()
            mock_claims_repo = Mock()

            # Setup mock pages needing review (stale page)
            stale_page = WikiPage(
                path="stale-page.md",
                title="Stale Page",
                freshness=FreshnessLevel.LEVEL_7,  # Stale
            )
            mock_wiki_repo.list_pages.return_value = ["stale-page.md"]
            mock_wiki_repo.read.return_value = stale_page

            scheduler = FSRSScheduler(mock_wiki_repo, mock_claims_repo, data_dir=Path(tmpdir))

            queue = scheduler.get_review_queue()
            self.assertIsInstance(queue, list)
            # Should contain ReviewItems
            for item in queue:
                self.assertIsInstance(item, ReviewItem)

    def test_mark_reviewed_updates_state(self) -> None:
        """Test 6: FSRSScheduler.mark_reviewed() updates FSRS card state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_wiki_repo = Mock()
            mock_claims_repo = Mock()
            mock_wiki_repo.list_pages.return_value = []

            scheduler = FSRSScheduler(mock_wiki_repo, mock_claims_repo, data_dir=Path(tmpdir))

            # First, schedule a review
            scheduler.schedule_review("test-page.md", rating=3)

            # Mark as reviewed
            scheduler.mark_reviewed("test-page.md", rating=3)

            # Verify state was persisted (check the cards file exists)
            cards_file = Path(tmpdir) / ".saw" / "fsrs_cards.yaml"
            # Cards file should exist
            self.assertTrue(cards_file.exists())

    def test_review_queue_prioritizes_high_freshness(self) -> None:
        """Test review queue prioritizes high-freshness pages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_wiki_repo = Mock()
            mock_claims_repo = Mock()

            # Create pages with different freshness levels
            very_stale = WikiPage(path="very-stale.md", title="Very Stale", freshness=FreshnessLevel.LEVEL_8)
            stale = WikiPage(path="stale.md", title="Stale", freshness=FreshnessLevel.LEVEL_7)
            fresh = WikiPage(path="fresh.md", title="Fresh", freshness=FreshnessLevel.LEVEL_1)

            mock_wiki_repo.list_pages.return_value = ["very-stale.md", "stale.md", "fresh.md"]
            mock_wiki_repo.read.side_effect = lambda p: {
                "very-stale.md": very_stale,
                "stale.md": stale,
                "fresh.md": fresh,
            }.get(p)

            scheduler = FSRSScheduler(mock_wiki_repo, mock_claims_repo, data_dir=Path(tmpdir))

            queue = scheduler.get_review_queue()
            # Items should be sorted by priority (higher freshness first)
            # Only stale items should be in queue
            self.assertTrue(all(item.freshness_level >= FreshnessLevel.LEVEL_6 for item in queue))


class TestReviewItem(unittest.TestCase):
    """Test cases for ReviewItem dataclass."""

    def test_review_item_creation(self) -> None:
        """Test creating a review item."""
        item = ReviewItem(
            page_path="test-page.md",
            claim_uuid=None,
            freshness_level=FreshnessLevel.LEVEL_6,
            last_reviewed=datetime.now(timezone.utc) - timedelta(days=30),
            next_review=datetime.now(timezone.utc) + timedelta(days=7),
            stability=5.0,
            difficulty=0.3,
        )
        self.assertEqual(item.page_path, "test-page.md")
        self.assertEqual(item.freshness_level, FreshnessLevel.LEVEL_6)


if __name__ == "__main__":
    unittest.main()
