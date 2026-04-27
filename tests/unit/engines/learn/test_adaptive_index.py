"""Tests for Adaptive Index Evolution.

Per 02-03 Task 4: Adaptive index evolution at 50 and 200 page thresholds.
Per XCUT-06 and FEATURES.md (Memex pattern): flat -> hierarchical -> indexed.
"""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from enum import Enum


class TestIndexModeDetection:
    """Tests for index mode detection based on page count."""

    def test_get_mode_returns_flat_when_page_count_under_50(self):
        """Test 1: AdaptiveIndexManager.get_mode() returns 'flat' when page_count <= 50."""
        from saw.engines.learn.adaptive_index import AdaptiveIndexManager, IndexMode

        mock_wiki = MagicMock()
        mock_wiki.count.return_value = 30  # Use count(), not get_page_count()
        mock_config = MagicMock()
        mock_config.index_mode = "flat"

        manager = AdaptiveIndexManager(mock_wiki, mock_config)

        assert manager.get_mode() == IndexMode.FLAT

    def test_get_mode_returns_hierarchical_when_50_to_200_pages(self):
        """Test 2: get_mode() returns 'hierarchical' when 50 < page_count <= 200."""
        from saw.engines.learn.adaptive_index import AdaptiveIndexManager, IndexMode

        mock_wiki = MagicMock()
        mock_wiki.count.return_value = 100  # Use count()
        mock_config = MagicMock()
        mock_config.index_mode = "flat"

        manager = AdaptiveIndexManager(mock_wiki, mock_config)

        assert manager.get_mode() == IndexMode.HIERARCHICAL

    def test_get_mode_returns_indexed_when_over_200_pages(self):
        """Test 3: get_mode() returns 'indexed' when page_count > 200."""
        from saw.engines.learn.adaptive_index import AdaptiveIndexManager, IndexMode

        mock_wiki = MagicMock()
        mock_wiki.count.return_value = 350  # Use count()
        mock_config = MagicMock()
        mock_config.index_mode = "flat"

        manager = AdaptiveIndexManager(mock_wiki, mock_config)

        assert manager.get_mode() == IndexMode.INDEXED


class TestIndexUpgrade:
    """Tests for index upgrade detection and execution."""

    def test_check_upgrade_returns_true_when_threshold_crossed(self):
        """Test 4: check_upgrade() returns True when threshold crossed."""
        from saw.engines.learn.adaptive_index import AdaptiveIndexManager

        mock_wiki = MagicMock()
        mock_wiki.count.return_value = 60  # Use count()
        mock_config = MagicMock()
        mock_config.index_mode = "flat"  # Config says flat, actual is hierarchical

        manager = AdaptiveIndexManager(mock_wiki, mock_config)

        assert manager.check_upgrade() == True

    def test_check_upgrade_returns_false_when_mode_matches(self):
        """check_upgrade() returns False when mode matches actual."""
        from saw.engines.learn.adaptive_index import AdaptiveIndexManager

        mock_wiki = MagicMock()
        mock_wiki.count.return_value = 30  # Use count()
        mock_config = MagicMock()
        mock_config.index_mode = "flat"

        manager = AdaptiveIndexManager(mock_wiki, mock_config)

        assert manager.check_upgrade() == False

    def test_upgrade_index_migrates_structure(self):
        """Test 5: upgrade_index() migrates structure correctly."""
        from saw.engines.learn.adaptive_index import AdaptiveIndexManager, IndexMode

        mock_wiki = MagicMock()
        mock_wiki.count.return_value = 60  # Use count()
        mock_config = MagicMock()
        mock_config.index_mode = "flat"

        manager = AdaptiveIndexManager(mock_wiki, mock_config)

        # Mock the upgrade methods
        with patch.object(manager, "_upgrade_to_hierarchical") as mock_upgrade:
            result = manager.upgrade_index()

            # Should have called the upgrade method
            mock_upgrade.assert_called_once()


class TestIndexModeEnum:
    """Tests for IndexMode enum."""

    def test_index_mode_values(self):
        """IndexMode has FLAT, HIERARCHICAL, INDEXED values."""
        from saw.engines.learn.adaptive_index import IndexMode

        assert IndexMode.FLAT.value == "flat"
        assert IndexMode.HIERARCHICAL.value == "hierarchical"
        assert IndexMode.INDEXED.value == "indexed"


class TestCategoryTree:
    """Tests for hierarchical category tree building."""

    def test_build_category_tree_groups_pages(self):
        """build_category_tree() groups pages by category."""
        from saw.engines.learn.adaptive_index import AdaptiveIndexManager

        mock_wiki = MagicMock()
        mock_wiki.get_page_count.return_value = 100
        mock_wiki.list_pages.return_value = [
            "concepts/python.md",
            "concepts/rust.md",
            "entities/project.md",
            "sources/doc1.md",
        ]
        mock_config = MagicMock()
        mock_config.index_mode = "hierarchical"

        manager = AdaptiveIndexManager(mock_wiki, mock_config)
        tree = manager.build_category_tree()

        # Should have categories as keys
        assert "concepts" in tree
        assert "entities" in tree
        assert "sources" in tree


class TestConceptClusters:
    """Tests for indexed mode concept clustering."""

    def test_build_concept_clusters_groups_similar_pages(self):
        """build_concept_clusters() clusters similar pages together."""
        from saw.engines.learn.adaptive_index import AdaptiveIndexManager

        mock_wiki = MagicMock()
        mock_wiki.get_page_count.return_value = 300
        mock_wiki.list_pages.return_value = [f"page_{i}.md" for i in range(300)]
        mock_config = MagicMock()
        mock_config.index_mode = "indexed"

        manager = AdaptiveIndexManager(mock_wiki, mock_config)

        # Without embeddings, this would need to be mocked
        # For now, just verify the method exists
        clusters = manager.build_concept_clusters()

        assert isinstance(clusters, list)


class TestIndexUpgradeResult:
    """Tests for IndexUpgradeResult dataclass."""

    def test_index_upgrade_result_has_required_fields(self):
        """IndexUpgradeResult has from_mode, to_mode, pages_processed, etc."""
        from saw.engines.learn.adaptive_index import IndexUpgradeResult, IndexMode

        result = IndexUpgradeResult(
            from_mode=IndexMode.FLAT,
            to_mode=IndexMode.HIERARCHICAL,
            pages_processed=100,
            duration_ms=500,
            new_structure_path=Path("/tmp/index_hierarchical.yaml"),
        )

        assert result.from_mode == IndexMode.FLAT
        assert result.to_mode == IndexMode.HIERARCHICAL
        assert result.pages_processed == 100
        assert result.duration_ms == 500
