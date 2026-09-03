"""Learn Engine - orchestrates all learning mechanisms.

Per D-14: Dependency order - Training Period → Expiry → FSRS → Feedback → Distillation → Trends.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import yaml

from saw.engines.learn.adaptive import TrainingPeriod
from saw.engines.learn.fsrs_scheduler import FSRSScheduler, ReviewItem

if TYPE_CHECKING:
    from saw.config.settings import WikiSettings
    from saw.domain.protocols import ClaimsRepository, WikiRepository
    from saw.adapters.llm.router import LLMRouter
    from saw.engines.learn.distiller import Distiller
    from saw.engines.learn.trends import TrendSenser


@dataclass
class LearningReport:
    """Report from daily learning tasks.

    Attributes:
        timestamp: When the report was generated
        preferences_learned: Number of new preferences learned
        sops_extracted: Number of SOPs extracted
        gaps_detected: Number of knowledge gaps found
        review_queue_size: Size of the review queue
        expiry_candidates: Number of expiry candidates identified
    """
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    preferences_learned: int = 0
    sops_extracted: int = 0
    gaps_detected: int = 0
    review_queue_size: int = 0
    expiry_candidates: int = 0


class LearnEngine:
    """Orchestrates all learning mechanisms.

    Coordinates:
    - Training period adaptation
    - FSRS spaced repetition
    - Cognitive distillation
    - Knowledge expiry tracking
    - Trend sensing
    - Feedback collection
    """

    def __init__(
        self,
        settings: WikiSettings,
        claims_repo: ClaimsRepository,
        wiki_repo: WikiRepository,
        llm_router: LLMRouter,
        distiller: Distiller | None = None,
        trends_senser: TrendSenser | None = None,
    ) -> None:
        self._settings = settings
        self._claims = claims_repo
        self._wiki = wiki_repo
        self._llm = llm_router

        # Initialize components
        self._training = TrainingPeriod(settings)
        self._fsrs = FSRSScheduler(wiki_repo, claims_repo)

        # Optional components (can be injected)
        self._distiller = distiller
        self._trends = trends_senser

        # Feedback file paths
        self._feedback_dir = settings.path / ".saw" / "feedback"

    def run_daily_learning(self) -> LearningReport:
        """Run scheduled learning tasks.

        Returns:
            LearningReport with results of all learning tasks.
        """
        report = LearningReport()

        # 1. Update preferences from training period
        if self._training.is_active():
            report.preferences_learned = len(self._training.get_learned_preferences())

        # 2. Run distillation if distiller available
        if self._distiller:
            approved_file = self._feedback_dir / "approved.yaml"
            if approved_file.is_file():
                sops = self._distiller.run_distillation(approved_file)
                report.sops_extracted = len(sops)

        # 3. Detect trends if senser available
        if self._trends:
            gaps = self._trends.detect_gaps()
            report.gaps_detected = len(gaps)

        # 4. Get review queue size
        queue = self._fsrs.get_review_queue()
        report.review_queue_size = len(queue)

        return report

    def apply_learned_preferences(self, content: str) -> str:
        """Apply learned preferences to content.

        Args:
            content: Content to modify.

        Returns:
            Modified content based on learned patterns.
        """
        return self._training.apply_preferences(content)

    def get_review_queue(self) -> list[ReviewItem]:
        """Get pages needing review.

        Returns:
            List of ReviewItems sorted by priority.
        """
        return self._fsrs.get_review_queue()

    def record_feedback(
        self,
        action: str,
        approved: bool,
        context: str,
    ) -> None:
        """Record user feedback for learning (per D-20).

        Per D-20: Edit implies implicit acceptance, reject requires explicit action.

        Args:
            action: The action type (e.g., "entity_extraction", "claim_extraction")
            approved: Whether the action was approved
            context: Context about the action
        """
        self._feedback_dir.mkdir(parents=True, exist_ok=True)

        # Determine which file to write to
        if approved:
            feedback_file = self._feedback_dir / "approved.yaml"
        else:
            feedback_file = self._feedback_dir / "rejected.yaml"

        # Load existing feedback
        existing: list[dict] = []
        if feedback_file.is_file():
            try:
                with open(feedback_file, encoding="utf-8") as f:
                    existing = yaml.safe_load(f) or []
            except yaml.YAMLError:
                existing = []

        # Append new feedback
        entry = {
            "action": action,
            "pattern": context,
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        existing.append(entry)

        # Write back
        with open(feedback_file, "w", encoding="utf-8") as f:
            yaml.dump(existing, f, default_flow_style=False, allow_unicode=True)

    def get_training_progress(self) -> dict:
        """Get training period progress.

        Returns:
            Dict with training status information.
        """
        return {
            "active": self._training.is_active(),
            "days_remaining": self._training.days_remaining(),
            "preferences_count": len(self._training.get_learned_preferences()),
        }
