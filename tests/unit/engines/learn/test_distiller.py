"""Tests for Distiller - SOP extraction from approved patterns.

Per D-19: SOP extraction from user feedback patterns.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock

from saw.engines.learn.distiller import Distiller, SOP


class TestDistiller(unittest.TestCase):
    """Test cases for cognitive distillation."""

    def test_extract_sop_returns_sop(self) -> None:
        """Test 1: Distiller.extract_sop() generates SOP from approved patterns."""
        mock_llm_router = Mock()

        # Mock LLM response for SOP extraction
        mock_llm_router.extract_claims.return_value = {
            "name": "Entity Naming Convention",
            "trigger": "When extracting entity names from documents",
            "steps": [
                "Prefer full entity names over abbreviations",
                "Use title case for proper nouns",
                "Include disambiguation context when ambiguous",
            ],
            "source_patterns": ["GPT-4 over gpt4", "Claude over claude"],
        }

        distiller = Distiller(mock_llm_router)

        approved_patterns = [
            "User accepted 'GPT-4' instead of 'gpt4'",
            "User accepted 'Claude' instead of 'claude'",
        ]

        sop = distiller.extract_sop(approved_patterns)

        self.assertIsInstance(sop, SOP)
        self.assertEqual(sop.name, "Entity Naming Convention")

    def test_run_distillation_processes_file(self) -> None:
        """Test run_distillation processes approved.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            approved_file = Path(tmpdir) / "approved.yaml"

            # Create approved.yaml content with multiple patterns for same action
            approved_content = """- action: entity_extraction
  pattern: Prefer full entity names over abbreviations
  context: User accepted 'GPT-4' instead of 'gpt4'
  timestamp: "2026-04-26T10:00:00Z"
- action: entity_extraction
  pattern: Use title case for proper nouns
  context: User accepted 'Claude' over 'claude'
  timestamp: "2026-04-26T10:01:00Z"
"""
            approved_file.write_text(approved_content)

            mock_llm_router = Mock()
            mock_llm_router.extract_claims.return_value = {
                "name": "Entity Naming",
                "trigger": "When extracting entity names",
                "steps": ["Use full names"],
                "source_patterns": ["GPT-4 over gpt4"],
            }

            distiller = Distiller(mock_llm_router, sops_dir=Path(tmpdir))
            sops = distiller.run_distillation(approved_file)

            self.assertIsInstance(sops, list)
            self.assertEqual(len(sops), 1)


class TestSOP(unittest.TestCase):
    """Test cases for SOP dataclass."""

    def test_sop_creation(self) -> None:
        """Test creating an SOP."""
        from datetime import datetime, timezone

        sop = SOP(
            name="Test SOP",
            trigger="When testing",
            steps=["Step 1", "Step 2"],
            source_patterns=["pattern1", "pattern2"],
            created_at=datetime.now(timezone.utc),
        )

        self.assertEqual(sop.name, "Test SOP")
        self.assertEqual(len(sop.steps), 2)


if __name__ == "__main__":
    unittest.main()
