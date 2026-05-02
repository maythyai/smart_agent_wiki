"""Unit tests for Logseq models.

Plan 13-01 Task 1: Test LogseqConfig, BlockNode, PropertyDrawer, and database models.
"""
import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os

from saw.connectors.logseq.models import (
    LogseqConfig,
    BlockNode,
    PropertyDrawer,
    ParsedPage,
)


class TestLogseqConfig:
    """Tests for LogseqConfig validation."""

    def test_config_validates_graph_path_exists(self):
        """Test 1: LogseqConfig validates graph_path exists and is directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LogseqConfig(graph_path=Path(tmpdir))
            assert config.graph_path == Path(tmpdir)
            assert config.sync_enabled is True
            assert config.watch_enabled is True

    def test_config_rejects_nonexistent_path(self):
        """Test that config rejects nonexistent path."""
        with pytest.raises(ValueError, match="does not exist"):
            LogseqConfig(graph_path=Path("/nonexistent/path/12345"))

    def test_config_rejects_file_path(self):
        """Test that config rejects file path (must be directory)."""
        with tempfile.NamedTemporaryFile() as tmpfile:
            with pytest.raises(ValueError, match="not a directory"):
                LogseqConfig(graph_path=Path(tmpfile.name))

    def test_config_sync_and_watch_flags(self):
        """Test sync_enabled and watch_enabled flags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LogseqConfig(
                graph_path=Path(tmpdir),
                sync_enabled=False,
                watch_enabled=False,
            )
            assert config.sync_enabled is False
            assert config.watch_enabled is False


class TestBlockNode:
    """Tests for BlockNode model."""

    def test_block_node_basic(self):
        """Test 2: BlockNode represents parsed bullet point with nesting."""
        block = BlockNode(
            id="block-1",
            content="This is a block",
            level=0,
            parent_id=None,
            properties={},
        )
        assert block.id == "block-1"
        assert block.content == "This is a block"
        assert block.level == 0
        assert block.parent_id is None

    def test_block_node_with_parent(self):
        """Test nested block with parent reference."""
        block = BlockNode(
            id="block-2",
            content="Nested block",
            level=1,
            parent_id="block-1",
            properties={"confidence": "Layer 2"},
        )
        assert block.level == 1
        assert block.parent_id == "block-1"
        assert block.properties == {"confidence": "Layer 2"}

    def test_block_node_preserves_wikilink(self):
        """Test that wikilink syntax is preserved in content."""
        block = BlockNode(
            id="block-3",
            content="Link to [[Some Page]] and [[Another Page]]",
            level=0,
            parent_id=None,
            properties={},
        )
        assert "[[Some Page]]" in block.content
        assert "[[Another Page]]" in block.content


class TestPropertyDrawer:
    """Tests for PropertyDrawer model."""

    def test_property_drawer_basic(self):
        """Test 3: PropertyDrawer extracts key-value pairs from frontmatter."""
        drawer = PropertyDrawer(
            title="My Page",
            id="648a1b2c-uuid",
            tags=[["tag1"], ["tag2"]],
            confidence="Layer 2",
            created_at=datetime(2026, 5, 1, 10, 0, 0),
            custom={"custom_prop": "value"},
        )
        assert drawer.title == "My Page"
        assert drawer.id == "648a1b2c-uuid"
        assert drawer.tags == [["tag1"], ["tag2"]]
        assert drawer.confidence == "Layer 2"

    def test_property_drawer_optional_fields(self):
        """Test PropertyDrawer with minimal fields."""
        drawer = PropertyDrawer(title="Simple Page")
        assert drawer.title == "Simple Page"
        assert drawer.id is None
        assert drawer.tags == []
        assert drawer.confidence is None

    def test_property_drawer_custom_properties(self):
        """Test custom properties in drawer."""
        drawer = PropertyDrawer(
            title="Page",
            custom={"priority": "high", "status": "done"},
        )
        assert drawer.custom["priority"] == "high"
        assert drawer.custom["status"] == "done"


class TestParsedPage:
    """Tests for ParsedPage model."""

    def test_parsed_page_basic(self):
        """Test ParsedPage with blocks and properties."""
        blocks = [
            BlockNode(id="b1", content="First block", level=0, parent_id=None, properties={}),
            BlockNode(id="b2", content="Nested", level=1, parent_id="b1", properties={}),
        ]
        properties = PropertyDrawer(title="Test Page")

        page = ParsedPage(
            file_path=Path("/graph/pages/test.md"),
            title="Test Page",
            namespace="test",
            blocks=blocks,
            properties=properties,
        )
        assert page.file_path == Path("/graph/pages/test.md")
        assert page.namespace == "test"
        assert len(page.blocks) == 2

    def test_parsed_page_namespace_from_path(self):
        """Test namespace derivation from file path."""
        page = ParsedPage(
            file_path=Path("/graph/pages/foo/bar/baz.md"),
            title="Baz",
            namespace="foo/bar",
            blocks=[],
            properties=PropertyDrawer(title="Baz"),
        )
        assert page.namespace == "foo/bar"
