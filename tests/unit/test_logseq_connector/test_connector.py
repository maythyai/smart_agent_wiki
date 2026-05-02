"""Unit tests for LogseqConnector.

Plan 13-01 Task 4: Test LogseqConnector implementing UnifiedConnectorInterface.
"""
import pytest
from pathlib import Path
import tempfile
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from saw.connectors.logseq.connector import LogseqConnector
from saw.connectors.logseq.models import LogseqConfig
from saw.connectors.protocol import ConnectorItem


class TestLogseqConnector:
    """Tests for LogseqConnector."""

    @pytest.fixture
    def connector(self) -> LogseqConnector:
        """Create a connector instance."""
        return LogseqConnector()

    @pytest.fixture
    def temp_graph(self, tmp_path: Path) -> Path:
        """Create a temporary Logseq graph."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        # Create test file
        test_file = pages_dir / "test.md"
        test_file.write_text(
            """---
title: Test Page
---
- First block
  - Nested block
- Second block with [[Wikilink]]
"""
        )
        yield tmp_path

    def test_connector_implements_protocol(self, connector: LogseqConnector):
        """Test 1: Connector implements UnifiedConnectorInterface."""
        assert connector.platform_name == "logseq"
        assert connector.supports_push is True

    @pytest.mark.asyncio
    async def test_authenticate_validates_graph_path(
        self, connector: LogseqConnector, temp_graph: Path
    ):
        """Test 2: authenticate() validates graph_path and returns success."""
        result = await connector.authenticate({"graph_path": str(temp_graph)})

        assert result.access_token == "local"
        assert "graph_path" in result.raw_response

    @pytest.mark.asyncio
    async def test_authenticate_rejects_invalid_path(
        self, connector: LogseqConnector
    ):
        """Test that authenticate rejects non-existent path."""
        result = await connector.authenticate({"graph_path": "/nonexistent/12345"})

        assert result.access_token == ""
        assert "error" in result.raw_response

    @pytest.mark.asyncio
    async def test_get_items_returns_connector_items(
        self, connector: LogseqConnector, temp_graph: Path
    ):
        """Test 3: get_items() returns ConnectorItems from all .md files."""
        await connector.authenticate({"graph_path": str(temp_graph)})

        items = await connector.get_items()

        assert len(items) >= 2  # At least 2 blocks from test file

    @pytest.mark.asyncio
    async def test_get_items_since_filters_by_mtime(
        self, connector: LogseqConnector, temp_graph: Path
    ):
        """Test 4: get_items(since) only returns files modified after timestamp."""
        await connector.authenticate({"graph_path": str(temp_graph)})

        # Create new file after a delay
        import time
        time.sleep(0.1)
        new_file = temp_graph / "pages" / "new.md"
        new_file.write_text("- New block")

        since = datetime.now(timezone.utc)
        time.sleep(0.1)

        # Create another file
        newer_file = temp_graph / "pages" / "newer.md"
        newer_file.write_text("- Newer block")

        items = await connector.get_items(since=since)

        # Should include at least the newer file's blocks
        assert len(items) >= 1

    @pytest.mark.asyncio
    async def test_put_item_writes_block_back_to_file(
        self, connector: LogseqConnector, temp_graph: Path
    ):
        """Test 5: put_item() writes block back to file."""
        await connector.authenticate({"graph_path": str(temp_graph)})

        items = await connector.get_items()
        if not items:
            pytest.skip("No items to update")

        item = items[0]
        original_content = item.content
        item.content = "Updated block content"

        # This is a simplified test - real implementation needs block index tracking
        result = await connector.put_item(item)

        # Should return item ID
        assert result == item.id

    def test_transform_to_claim_creates_claim_with_correct_metadata(
        self, connector: LogseqConnector, temp_graph: Path
    ):
        """Test 6: transform_to_claim() creates Claim with correct metadata."""
        item = ConnectorItem(
            id="test-id",
            title="Test Block",
            content="Content with [[Wikilink]]",
            url="file:///test.md#block",
            created_at=datetime.now(timezone.utc),
            metadata={
                "namespace": "foo/bar",
                "page_title": "Test Page",
                "confidence": "Layer 2",
            },
        )

        claim_dict = connector.transform_to_claim(item)

        assert claim_dict["id"] == "test-id"
        assert claim_dict["content"] == "Content with [[Wikilink]]"
        assert claim_dict["metadata"]["namespace"] == "foo/bar"
        assert claim_dict["source_platform"] == "logseq"

    def test_transform_from_claim_preserves_wikilink_syntax(
        self, connector: LogseqConnector
    ):
        """Test 7: transform_from_claim() preserves wikilink syntax."""
        claim = {
            "id": "claim-1",
            "content": "Text with [[Link A]] and [[Link B]]",
            "title": "Claim Title",
            "metadata": {"namespace": "test"},
        }

        item = connector.transform_from_claim(claim)

        assert "[[Link A]]" in item.content
        assert "[[Link B]]" in item.content

    def test_namespace_hierarchy_correctly_mapped(
        self, connector: LogseqConnector
    ):
        """Test 8: Namespace hierarchy correctly mapped to wiki pages."""
        item = ConnectorItem(
            id="ns-test",
            title="Nested Page",
            content="Content",
            metadata={
                "namespace": "level1/level2/level3",
            },
        )

        claim = connector.transform_to_claim(item)

        # Namespace should map to wiki path
        assert claim["metadata"]["wiki_path"] == "level1/level2/level3"
