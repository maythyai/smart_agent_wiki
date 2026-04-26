"""Training period adaptation - learning user preferences during first 30 days.

Per D-15: Real-time adjustment during training period
Per D-16: Default 30 days, configurable
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from saw.config.settings import WikiSettings


@dataclass
class UserPreference:
    """A learned user preference pattern.

    Attributes:
        preference_type: Category of preference (tag_style, page_structure, entity_format)
        pattern: The observed pattern
        confidence: How confident the system is (0.0 to 1.0)
        source: "explicit" (user stated) or "implicit" (observed behavior)
    """
    preference_type: str
    pattern: str
    confidence: float
    source: str  # "explicit" or "implicit"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TrainingPeriod:
    """Manages the 30-day training period for user preference learning.

    During the training period, the system learns from user behavior
    and applies preferences in real-time (per D-15).

    Training period state is persisted in .saw/training.yaml.
    """

    DEFAULT_DURATION_DAYS = 30  # Per D-16

    def __init__(
        self,
        settings: WikiSettings,
        start_date: datetime | None = None,
    ) -> None:
        self._settings = settings
        self._duration = timedelta(days=self.DEFAULT_DURATION_DAYS)
        self._preferences: list[UserPreference] = []
        self._start_date: datetime | None = start_date

        # Load state from file
        self._load_state()

    def _load_state(self) -> None:
        """Load training state from .saw/training.yaml."""
        state_file = self._get_state_file()
        if state_file.is_file():
            try:
                with open(state_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                if data.get("start_date"):
                    self._start_date = datetime.fromisoformat(data["start_date"])
                if data.get("preferences"):
                    for pref_data in data["preferences"]:
                        self._preferences.append(UserPreference(
                            preference_type=pref_data.get("preference_type", ""),
                            pattern=pref_data.get("pattern", ""),
                            confidence=pref_data.get("confidence", 0.5),
                            source=pref_data.get("source", "implicit"),
                        ))
            except (yaml.YAMLError, ValueError):
                pass  # Start fresh on error

    def _save_state(self) -> None:
        """Save training state to .saw/training.yaml."""
        state_file = self._get_state_file()
        state_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "start_date": (self._start_date or datetime.now(timezone.utc)).isoformat(),
            "duration_days": self.DEFAULT_DURATION_DAYS,
            "preferences": [
                {
                    "preference_type": p.preference_type,
                    "pattern": p.pattern,
                    "confidence": p.confidence,
                    "source": p.source,
                    "timestamp": p.timestamp.isoformat(),
                }
                for p in self._preferences
            ],
        }

        with open(state_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    def _get_state_file(self) -> Path:
        """Get path to training state file."""
        return self._settings.path / ".saw" / "training.yaml"

    def is_active(self) -> bool:
        """Check if currently in training period (per D-16).

        Returns:
            True if within training period, False otherwise.
        """
        if self._start_date is None:
            return True  # Start date not set, assume active

        end_date = self._start_date + self._duration
        return datetime.now(timezone.utc) < end_date

    def days_remaining(self) -> int:
        """Get number of days remaining in training period.

        Returns:
            Number of days remaining (0 if not active).
        """
        if self._start_date is None:
            return self.DEFAULT_DURATION_DAYS

        end_date = self._start_date + self._duration
        remaining = end_date - datetime.now(timezone.utc)

        return max(0, remaining.days)

    def record_preference(self, preference: UserPreference) -> None:
        """Store a user preference pattern (per D-15).

        Args:
            preference: The preference to record.
        """
        self._preferences.append(preference)
        self._save_state()

    def get_learned_preferences(self) -> list[UserPreference]:
        """Get accumulated preferences.

        Returns:
            List of all learned preferences.
        """
        return list(self._preferences)

    def apply_preferences(self, content: str) -> str:
        """Apply learned preferences to content (per D-15 real-time adjustment).

        This method would apply learned patterns to modify content
        during the training period.

        Args:
            content: The content to apply preferences to.

        Returns:
            Modified content based on learned preferences.
        """
        # Placeholder - in production, this would apply learned patterns
        # For example:
        # - Expand abbreviations if preference is "full names"
        # - Adjust tag formatting based on "tag_style" preference
        # - Restructure content based on "page_structure" preference

        return content
