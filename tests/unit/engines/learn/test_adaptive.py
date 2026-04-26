"""Tests for TrainingPeriod - user preference learning during first 30 days.

Per D-15, D-16:
- D-15: Training period real-time adjustment
- D-16: Default 30 days, user configurable
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from saw.config.settings import WikiSettings
from saw.engines.learn.adaptive import TrainingPeriod, UserPreference


class TestTrainingPeriod(unittest.TestCase):
    """Test cases for training period adaptation."""

    def test_is_active_during_first_30_days(self) -> None:
        """Test 1: TrainingPeriod.is_active() returns True during first 30 days (per D-16)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = WikiSettings(path=Path(tmpdir))
            training = TrainingPeriod(settings, start_date=datetime.now(timezone.utc))
            self.assertTrue(training.is_active())

    def test_is_active_false_after_30_days(self) -> None:
        """Test training period ends after 30 days."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = WikiSettings(path=Path(tmpdir))
            # Start 31 days ago
            start = datetime.now(timezone.utc) - timedelta(days=31)
            training = TrainingPeriod(settings, start_date=start)
            self.assertFalse(training.is_active())

    def test_days_remaining(self) -> None:
        """Test 2: TrainingPeriod.days_remaining() returns correct count."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = WikiSettings(path=Path(tmpdir))
            training = TrainingPeriod(settings, start_date=datetime.now(timezone.utc))
            # Should have ~30 days remaining
            remaining = training.days_remaining()
            self.assertGreaterEqual(remaining, 29)
            self.assertLessEqual(remaining, 30)

    def test_record_preference(self) -> None:
        """Test 2: TrainingPeriod.record_preference() stores user preference pattern."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = WikiSettings(path=Path(tmpdir))
            training = TrainingPeriod(settings)

            pref = UserPreference(
                preference_type="tag_style",
                pattern="Prefer descriptive tags over single words",
                confidence=0.8,
                source="implicit",
            )
            training.record_preference(pref)

            prefs = training.get_learned_preferences()
            self.assertEqual(len(prefs), 1)
            self.assertEqual(prefs[0].preference_type, "tag_style")

    def test_get_learned_preferences(self) -> None:
        """Test 3: TrainingPeriod.get_learned_preferences() returns accumulated preferences."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = WikiSettings(path=Path(tmpdir))
            training = TrainingPeriod(settings)

            # Add multiple preferences
            training.record_preference(UserPreference(
                preference_type="tag_style",
                pattern="Pattern 1",
                confidence=0.8,
                source="implicit",
            ))
            training.record_preference(UserPreference(
                preference_type="page_structure",
                pattern="Pattern 2",
                confidence=0.9,
                source="explicit",
            ))

            prefs = training.get_learned_preferences()
            self.assertEqual(len(prefs), 2)

    def test_apply_preferences(self) -> None:
        """Test applying learned preferences to content (per D-15)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            settings = WikiSettings(path=Path(tmpdir))
            training = TrainingPeriod(settings)

            # Add a preference
            training.record_preference(UserPreference(
                preference_type="entity_format",
                pattern="Use full names instead of abbreviations",
                confidence=0.9,
                source="explicit",
            ))

            content = "GPT-4 is a model"
            # Apply preferences would modify content based on learned patterns
            result = training.apply_preferences(content)
            # For now, just verify it returns content
            self.assertIsInstance(result, str)


class TestUserPreference(unittest.TestCase):
    """Test cases for UserPreference dataclass."""

    def test_preference_creation(self) -> None:
        """Test creating a user preference."""
        pref = UserPreference(
            preference_type="tag_style",
            pattern="Prefer multi-word tags",
            confidence=0.85,
            source="implicit",
        )
        self.assertEqual(pref.preference_type, "tag_style")
        self.assertEqual(pref.confidence, 0.85)


if __name__ == "__main__":
    unittest.main()
