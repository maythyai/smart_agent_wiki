"""FSRS Scheduler - spaced repetition for page reviews.

Per D-17: FSRS algorithm for scheduling page reviews.
Uses the fsrs library for FSRS v6 algorithm implementation.

The scheduler manages review intervals for wiki pages based on:
- Current freshness level
- User ratings (1=Again, 2=Hard, 3=Good, 4=Easy)
- FSRS stability and difficulty parameters
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from fsrs import Scheduler, Card, Rating

from saw.domain.value_objects import FreshnessLevel

if TYPE_CHECKING:
    from saw.domain.protocols import ClaimsRepository, WikiRepository


@dataclass
class ReviewItem:
    """A page or claim scheduled for review.

    Attributes:
        page_path: Path to the wiki page
        claim_uuid: Optional claim UUID for claim-level reviews
        freshness_level: Current freshness level (used for priority)
        last_reviewed: When last reviewed
        next_review: Scheduled review date
        stability: FSRS stability parameter
        difficulty: FSRS difficulty parameter
    """
    page_path: str
    claim_uuid: str | None = None
    freshness_level: FreshnessLevel = FreshnessLevel.LEVEL_0
    last_reviewed: datetime | None = None
    next_review: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stability: float = 1.0
    difficulty: float = 0.3


class FSRSScheduler:
    """FSRS-based spaced repetition scheduler for page reviews.

    Manages review schedules using the FSRS v6 algorithm.
    High-freshness pages (>= LEVEL_6) are prioritized for review.
    """

    # Freshness threshold for review queue
    REVIEW_FRESHNESS_THRESHOLD = FreshnessLevel.LEVEL_6

    def __init__(
        self,
        wiki_repo: WikiRepository,
        claims_repo: ClaimsRepository,
        data_dir: Path | None = None,
    ) -> None:
        self._wiki = wiki_repo
        self._claims = claims_repo
        self._data_dir = data_dir or Path(".")
        self._fsrs = Scheduler()  # Use default parameters
        self._cards: dict[str, Card] = {}  # page_path -> FSRS Card

        # Load existing card states
        self._load_cards()

    def _load_cards(self) -> None:
        """Load FSRS card states from .saw/fsrs_cards.yaml."""
        cards_file = self._data_dir / ".saw" / "fsrs_cards.yaml"
        if cards_file.is_file():
            try:
                with open(cards_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                for page_path, card_data in data.items():
                    # Create Card from stored data using from_dict
                    self._cards[page_path] = Card.from_dict(card_data)
            except (yaml.YAMLError, ValueError):
                pass  # Start fresh on error

    def _save_cards(self) -> None:
        """Save FSRS card states to .saw/fsrs_cards.yaml."""
        cards_file = self._data_dir / ".saw" / "fsrs_cards.yaml"
        cards_file.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        for page_path, card in self._cards.items():
            # Use the card's to_dict method for serialization
            data[page_path] = card.to_dict()

        with open(cards_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)

    def schedule_review(self, page_path: str, rating: int) -> datetime:
        """Schedule next review using FSRS algorithm (per D-17).

        Args:
            page_path: Path to the wiki page.
            rating: User rating (1=Again, 2=Hard, 3=Good, 4=Easy).

        Returns:
            Next review datetime.
        """
        # Get or create card
        if page_path not in self._cards:
            self._cards[page_path] = Card()

        card = self._cards[page_path]

        # Map rating to FSRS Rating enum
        rating_map = {1: Rating.Again, 2: Rating.Hard, 3: Rating.Good, 4: Rating.Easy}
        fsrs_rating = rating_map.get(rating, Rating.Good)

        # Review using FSRS
        now = datetime.now(timezone.utc)
        new_card, _review_log = self._fsrs.review_card(card, fsrs_rating, now)

        self._cards[page_path] = new_card
        next_review = new_card.due or (now + timedelta(days=1))

        self._save_cards()
        return next_review

    def get_review_queue(self) -> list[ReviewItem]:
        """Get pages needing review sorted by priority (per D-17).

        Priority is based on freshness level - higher freshness
        (more stale) pages are reviewed first.

        Returns:
            List of ReviewItems sorted by priority.
        """
        queue: list[ReviewItem] = []

        # Get all pages and check freshness
        for page_path in self._wiki.list_pages():
            page = self._wiki.read(page_path)
            if page is None:
                continue

            # Include pages with high freshness (stale) or overdue reviews
            include = False
            freshness = page.freshness

            # Check if page is stale enough for review
            if freshness >= self.REVIEW_FRESHNESS_THRESHOLD:
                include = True

            # Check if card has an overdue review
            if page_path in self._cards:
                card = self._cards[page_path]
                if card.due and card.due <= datetime.now(timezone.utc):
                    include = True

            if include:
                last_reviewed = None
                stability = 1.0
                difficulty = 0.3
                next_review = datetime.now(timezone.utc)

                if page_path in self._cards:
                    card = self._cards[page_path]
                    last_reviewed = card.last_review
                    stability = card.stability
                    difficulty = card.difficulty
                    next_review = card.due or datetime.now(timezone.utc)

                queue.append(ReviewItem(
                    page_path=page_path,
                    freshness_level=freshness,
                    last_reviewed=last_reviewed,
                    next_review=next_review,
                    stability=stability,
                    difficulty=difficulty,
                ))

        # Sort by freshness (descending) and then by due date
        queue.sort(key=lambda x: (-x.freshness_level, x.next_review))

        return queue

    def mark_reviewed(self, page_path: str, rating: int) -> None:
        """Mark a page as reviewed with given rating.

        Updates the FSRS card state with the new rating.

        Args:
            page_path: Path to the reviewed page.
            rating: User rating (1=Again, 2=Hard, 3=Good, 4=Easy).
        """
        # This is essentially schedule_review but we call it separately
        # for clarity in the API
        self.schedule_review(page_path, rating)
