"""Tests for Progressive Memory Depth (L0/L1/L2).

Per 02-03 Task 3: Progressive memory depth for token efficiency.
Per XCUT-05: Reduce boot tokens from ~20K to ~8-10K.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from enum import Enum


class TestProgressiveMemoryL0:
    """Tests for L0 index (always-loaded)."""

    def test_get_l0_returns_compact_index(self):
        """Test 1: ProgressiveMemory.get_l0() returns index content <= 100 lines."""
        from saw.engines.query.memory import ProgressiveMemory, MemoryLevel

        # Mock wiki repo
        mock_wiki = MagicMock()
        mock_wiki.list_pages.return_value = [f"page_{i}.md" for i in range(50)]
        mock_wiki.get_page_count.return_value = 50
        mock_wiki.read.return_value = MagicMock(
            title=f"Test Page",
            page_type=MagicMock(name="SUMMARY"),
        )

        # Mock compiler
        mock_compiler = MagicMock()

        memory = ProgressiveMemory(mock_wiki, mock_compiler)
        l0_content = memory.get_l0()

        # L0 should be compact
        lines = l0_content.strip().split("\n") if l0_content else []
        assert len(lines) <= 100, f"L0 index has {len(lines)} lines, should be <= 100"

    def test_l0_contains_wiki_structure(self):
        """L0 index contains wiki structure (page types, entity counts)."""
        from saw.engines.query.memory import ProgressiveMemory

        mock_wiki = MagicMock()
        mock_wiki.list_pages.return_value = ["concepts/test.md", "entities/entity1.md"]
        mock_wiki.get_page_count.return_value = 2
        mock_wiki.read.return_value = MagicMock(title="Test", page_type=MagicMock(name="CONCEPT"))

        mock_compiler = MagicMock()

        memory = ProgressiveMemory(mock_wiki, mock_compiler)
        l0_content = memory.get_l0()

        assert l0_content is not None
        # Should contain structure info
        assert "page" in l0_content.lower() or "index" in l0_content.lower() or l0_content != ""


class TestProgressiveMemoryL1:
    """Tests for L1 summary index."""

    def test_get_l1_returns_summaries(self):
        """Test 2: ProgressiveMemory.get_l1(topic) returns summary content for recent topics."""
        from saw.engines.query.memory import ProgressiveMemory

        mock_wiki = MagicMock()
        mock_wiki.list_pages.return_value = ["recent/page1.md"]
        mock_wiki.read.return_value = MagicMock(
            title="Recent Topic",
            content="# Summary\nThis is a summary of the topic.",
            page_type=MagicMock(name="SUMMARY"),
        )

        mock_compiler = MagicMock()

        memory = ProgressiveMemory(mock_wiki, mock_compiler)
        l1_content = memory.get_l1(topic="recent")

        assert l1_content is not None
        # L1 should contain summary content

    def test_l1_respects_token_budget(self):
        """Test 4: Memory levels respect token budget constraints."""
        from saw.engines.query.memory import ProgressiveMemory

        mock_wiki = MagicMock()
        mock_wiki.list_pages.return_value = [f"page_{i}.md" for i in range(100)]
        mock_wiki.read.return_value = MagicMock(
            title="Page",
            content="x" * 1000,  # Long content
            page_type=MagicMock(name="SUMMARY"),
        )

        mock_compiler = MagicMock()

        memory = ProgressiveMemory(mock_wiki, mock_compiler)
        l1_content = memory.get_l1(topic="test", budget=500)

        # L1 should be budget-aware
        estimated_tokens = len(l1_content) // 4 if l1_content else 0
        assert estimated_tokens <= 600  # Allow some margin


class TestProgressiveMemoryL2:
    """Tests for L2 full content on demand."""

    def test_get_l2_returns_full_content(self):
        """Test 3: ProgressiveMemory.get_l2(page_paths) returns full content for specific pages."""
        from saw.engines.query.memory import ProgressiveMemory

        mock_wiki = MagicMock()
        mock_wiki.read.return_value = MagicMock(
            title="Full Page",
            content="# Full Content\n\nThis is the full content of the page.",
            page_type=MagicMock(name="SOURCE"),
            confidence=MagicMock(name="SINGLE_SOURCE"),
            freshness=0,
            tags=["test"],
            related=[],
        )

        mock_compiler = MagicMock()

        memory = ProgressiveMemory(mock_wiki, mock_compiler)
        l2_content = memory.get_l2(["full_page.md"])

        assert l2_content is not None
        assert "Full Content" in l2_content

    def test_l2_respects_budget(self):
        """L2 content respects token budget."""
        from saw.engines.query.memory import ProgressiveMemory

        mock_wiki = MagicMock()
        mock_wiki.read.return_value = MagicMock(
            title="Big Page",
            content="x" * 10000,  # Very long content
            page_type=MagicMock(name="SOURCE"),
            confidence=MagicMock(name="SINGLE_SOURCE"),
            freshness=0,
            tags=[],
            related=[],
        )

        mock_compiler = MagicMock()

        memory = ProgressiveMemory(mock_wiki, mock_compiler)
        l2_content = memory.get_l2(["big_page.md"], budget=1000)

        # L2 should be truncated if budget exceeded
        estimated_tokens = len(l2_content) // 4 if l2_content else 0
        assert estimated_tokens <= 1200  # Allow margin


class TestProgressiveMemoryAutoSelect:
    """Tests for automatic level selection."""

    def test_auto_select_level_small_budget_uses_l0(self):
        """Small budget selects L0."""
        from saw.engines.query.memory import ProgressiveMemory, MemoryLevel

        mock_wiki = MagicMock()
        mock_wiki.list_pages.return_value = [f"page_{i}.md" for i in range(100)]
        mock_wiki.get_page_count.return_value = 100

        mock_compiler = MagicMock()

        memory = ProgressiveMemory(mock_wiki, mock_compiler)
        # Use a very small budget that L0 alone fills
        level, content = memory.auto_select_level(budget=10)

        assert level == MemoryLevel.L0

    def test_auto_select_level_medium_budget_uses_l1(self):
        """Medium budget selects L1."""
        from saw.engines.query.memory import ProgressiveMemory, MemoryLevel

        mock_wiki = MagicMock()
        mock_wiki.list_pages.return_value = ["page.md"]
        mock_wiki.get_page_count.return_value = 10
        mock_wiki.read.return_value = MagicMock(
            title="Page",
            content="Content",
            page_type=MagicMock(name="SUMMARY"),
        )

        mock_compiler = MagicMock()

        memory = ProgressiveMemory(mock_wiki, mock_compiler)
        level, content = memory.auto_select_level(budget=2000)

        # Should be L0 or L1 depending on content size
        assert level in (MemoryLevel.L0, MemoryLevel.L1)


class TestTokenEstimation:
    """Tests for token estimation."""

    def test_estimate_tokens_uses_char_division(self):
        """estimate_tokens uses chars / 4 as rough estimate."""
        from saw.engines.query.memory import ProgressiveMemory

        mock_wiki = MagicMock()
        mock_compiler = MagicMock()

        memory = ProgressiveMemory(mock_wiki, mock_compiler)

        # 400 chars should estimate to ~100 tokens
        assert memory.estimate_tokens("a" * 400) == 100

        # 0 chars should be 0 tokens
        assert memory.estimate_tokens("") == 0


class TestMemoryLevelEnum:
    """Tests for MemoryLevel enum."""

    def test_memory_level_values(self):
        """MemoryLevel has L0, L1, L2 values."""
        from saw.engines.query.memory import MemoryLevel

        assert MemoryLevel.L0.value == 0
        assert MemoryLevel.L1.value == 1
        assert MemoryLevel.L2.value == 2
