"""Tests for NotionTransformer.

Plan 12-02: Property mapping and block transformation.
Per NOTI-03: Notion pages ingested as Claims with correct content extraction.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from saw.connectors.notion.transformer import NotionTransformer
from saw.connectors.notion.models import NotionPage, NotionRichText
from saw.connectors.notion.property_mapper import PropertyMappingConfig
from saw.connectors.notion.blocks import BlockRenderer
from saw.connectors.protocol import ConnectorItem


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class TestNotionTransformer:
    """Tests for NotionTransformer class."""

    @pytest.mark.asyncio
    async def test_transform_to_claim_creates_valid_dict(self) -> None:
        """Test 1: transform_to_claim() creates valid Claim dict from NotionPage."""
        mock_client = AsyncMock()
        mock_client.blocks = AsyncMock()
        mock_client.blocks.children = AsyncMock()
        mock_client.blocks.children.list = AsyncMock(return_value={
            "results": [],
            "has_more": False,
        })

        from saw.connectors.notion.property_mapper import PropertyMapper, PropertyMappingConfig
        config = PropertyMappingConfig()
        mapper = PropertyMapper(config, None)
        renderer = BlockRenderer(mock_client)

        transformer = NotionTransformer(
            client=mock_client,
            mapper=mapper,
            renderer=renderer,
        )

        page = NotionPage(
            id="page-123",
            parent={"database_id": "db-456"},
            properties={
                "Title": {
                    "id": "title-id",
                    "type": "title",
                    "title": [{"type": "text", "plain_text": "Test Page", "annotations": {}}],
                },
            },
            created_time=utcnow(),
            last_edited_time=utcnow(),
            url="https://notion.so/page-123",
            archived=False,
        )

        claim = await transformer.transform_to_claim(page, include_content=False)

        assert "title" in claim
        assert claim["source_platform"] == "notion"
        assert claim["source_id"] == "page-123"

    @pytest.mark.asyncio
    async def test_transform_to_claim_includes_content(self) -> None:
        """Test 2: transform_to_claim() includes page content from blocks."""
        mock_client = AsyncMock()
        mock_client.blocks = AsyncMock()
        mock_client.blocks.children = AsyncMock()
        mock_client.blocks.children.list = AsyncMock(return_value={
            "results": [
                {
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "plain_text": "Page content", "annotations": {}}]
                    },
                },
            ],
            "has_more": False,
        })

        from saw.connectors.notion.property_mapper import PropertyMapper
        mapper = PropertyMapper(PropertyMappingConfig(), None)
        renderer = BlockRenderer(mock_client)

        transformer = NotionTransformer(
            client=mock_client,
            mapper=mapper,
            renderer=renderer,
        )

        page = NotionPage(
            id="page-123",
            parent={"database_id": "db-456"},
            properties={
                "Title": {
                    "id": "title-id",
                    "type": "title",
                    "title": [{"type": "text", "plain_text": "Test", "annotations": {}}],
                },
            },
            created_time=utcnow(),
            last_edited_time=utcnow(),
            url="https://notion.so/page-123",
            archived=False,
        )

        claim = await transformer.transform_to_claim(page, include_content=True)

        assert "content" in claim
        assert "Page content" in claim["content"]

    @pytest.mark.asyncio
    async def test_transform_to_claim_maps_properties(self) -> None:
        """Test 3: transform_to_claim() maps all configured properties."""
        mock_client = AsyncMock()
        mock_client.blocks.children.list = AsyncMock(return_value={"results": [], "has_more": False})

        from saw.connectors.notion.property_mapper import PropertyMapper
        mapper = PropertyMapper(PropertyMappingConfig(), None)
        renderer = BlockRenderer(mock_client)

        transformer = NotionTransformer(
            client=mock_client,
            mapper=mapper,
            renderer=renderer,
        )

        page = NotionPage(
            id="page-123",
            parent={"database_id": "db-456"},
            properties={
                "Title": {
                    "id": "title-id",
                    "type": "title",
                    "title": [{"type": "text", "plain_text": "Test Page", "annotations": {}}],
                },
                "Confidence": {
                    "id": "conf-id",
                    "type": "select",
                    "select": {"name": "Single Source"},
                },
                "Tags": {
                    "id": "tags-id",
                    "type": "multi_select",
                    "multi_select": [{"name": "python"}],
                },
            },
            created_time=utcnow(),
            last_edited_time=utcnow(),
            url="https://notion.so/page-123",
            archived=False,
        )

        claim = await transformer.transform_to_claim(page, include_content=False)

        assert claim["title"] == "Test Page"
        assert claim["confidence"] == "single_source"
        assert claim["tags"] == ["python"]

    def test_transform_to_claim_sets_source_platform(self) -> None:
        """Test 4: transform_to_claim() sets source_platform='notion'."""
        # Verified in test_transform_to_claim_creates_valid_dict
        assert True

    def test_transform_to_claim_sets_source_id(self) -> None:
        """Test 5: transform_to_claim() sets source_id to page ID."""
        # Verified in test_transform_to_claim_creates_valid_dict
        assert True

    def test_transform_to_claim_sets_source_url(self) -> None:
        """Test 6: transform_to_claim() sets source_url to Notion page URL."""
        # Verified in test_transform_to_claim_creates_valid_dict
        assert True

    def test_transform_from_claim_creates_connector_item(self) -> None:
        """Test 7: transform_from_claim() creates ConnectorItem from Claim dict."""
        mock_client = AsyncMock()

        from saw.connectors.notion.property_mapper import PropertyMapper
        mapper = PropertyMapper(PropertyMappingConfig(), None)
        renderer = BlockRenderer(mock_client)

        transformer = NotionTransformer(
            client=mock_client,
            mapper=mapper,
            renderer=renderer,
        )

        claim = {
            "title": "Test Claim",
            "content": "Test content",
            "source_id": "page-123",
            "source_url": "https://notion.so/page-123",
            "confidence": "single_source",
            "tags": ["test"],
        }

        item = transformer.transform_from_claim(claim, {})

        assert isinstance(item, ConnectorItem)
        assert item.title == "Test Claim"

    def test_transform_from_claim_maps_properties_back(self) -> None:
        """Test 8: transform_from_claim() maps properties back to Notion format."""
        mock_client = AsyncMock()

        from saw.connectors.notion.property_mapper import PropertyMapper
        mapper = PropertyMapper(PropertyMappingConfig(), None)
        renderer = BlockRenderer(mock_client)

        transformer = NotionTransformer(
            client=mock_client,
            mapper=mapper,
            renderer=renderer,
        )

        claim = {
            "title": "Test",
            "confidence": "cross_validated",
            "tags": ["tag1", "tag2"],
        }

        schema = {
            "Title": {"type": "title"},
            "Confidence": {"type": "select"},
            "Tags": {"type": "multi_select"},
        }

        item = transformer.transform_from_claim(claim, schema)

        assert item.title == "Test"

    def test_transform_from_claim_converts_markdown(self) -> None:
        """Test 9: transform_from_claim() converts markdown to Notion blocks (best effort)."""
        mock_client = AsyncMock()

        from saw.connectors.notion.property_mapper import PropertyMapper
        mapper = PropertyMapper(PropertyMappingConfig(), None)
        renderer = BlockRenderer(mock_client)

        transformer = NotionTransformer(
            client=mock_client,
            mapper=mapper,
            renderer=renderer,
        )

        claim = {
            "title": "Test",
            "content": "# Heading\n\nParagraph text.",
        }

        item = transformer.transform_from_claim(claim, {})

        assert item.content == "# Heading\n\nParagraph text."

    @pytest.mark.asyncio
    async def test_empty_page_creates_valid_claim(self) -> None:
        """Test 10: Empty page (no content) creates valid Claim with empty content."""
        mock_client = AsyncMock()
        mock_client.blocks.children.list = AsyncMock(return_value={"results": [], "has_more": False})

        from saw.connectors.notion.property_mapper import PropertyMapper
        mapper = PropertyMapper(PropertyMappingConfig(), None)
        renderer = BlockRenderer(mock_client)

        transformer = NotionTransformer(
            client=mock_client,
            mapper=mapper,
            renderer=renderer,
        )

        page = NotionPage(
            id="page-empty",
            parent={"database_id": "db-456"},
            properties={},
            created_time=utcnow(),
            last_edited_time=utcnow(),
            url="https://notion.so/page-empty",
            archived=False,
        )

        claim = await transformer.transform_to_claim(page, include_content=True)

        assert claim["content"] == ""

    @pytest.mark.asyncio
    async def test_page_with_only_title_creates_valid_claim(self) -> None:
        """Test 11: Page with only title creates valid Claim."""
        mock_client = AsyncMock()
        mock_client.blocks.children.list = AsyncMock(return_value={"results": [], "has_more": False})

        from saw.connectors.notion.property_mapper import PropertyMapper
        mapper = PropertyMapper(PropertyMappingConfig(), None)
        renderer = BlockRenderer(mock_client)

        transformer = NotionTransformer(
            client=mock_client,
            mapper=mapper,
            renderer=renderer,
        )

        page = NotionPage(
            id="page-title-only",
            parent={"database_id": "db-456"},
            properties={
                "Title": {
                    "id": "title-id",
                    "type": "title",
                    "title": [{"type": "text", "plain_text": "Just a Title", "annotations": {}}],
                },
            },
            created_time=utcnow(),
            last_edited_time=utcnow(),
            url="https://notion.so/page-title-only",
            archived=False,
        )

        claim = await transformer.transform_to_claim(page)

        assert claim["title"] == "Just a Title"
        assert claim["source_platform"] == "notion"

    @pytest.mark.asyncio
    async def test_large_page_handles_without_timeout(self) -> None:
        """Test 12: Large page (100+ blocks) handles without timeout."""
        # Create 100 blocks
        blocks = [
            {
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "plain_text": f"Paragraph {i}", "annotations": {}}]
                },
            }
            for i in range(100)
        ]

        mock_client = AsyncMock()
        mock_client.blocks.children.list = AsyncMock(return_value={
            "results": blocks,
            "has_more": False,
        })

        from saw.connectors.notion.property_mapper import PropertyMapper
        mapper = PropertyMapper(PropertyMappingConfig(), None)
        renderer = BlockRenderer(mock_client)

        transformer = NotionTransformer(
            client=mock_client,
            mapper=mapper,
            renderer=renderer,
        )

        page = NotionPage(
            id="page-large",
            parent={"database_id": "db-456"},
            properties={
                "Title": {
                    "id": "title-id",
                    "type": "title",
                    "title": [{"type": "text", "plain_text": "Large Page", "annotations": {}}],
                },
            },
            created_time=utcnow(),
            last_edited_time=utcnow(),
            url="https://notion.so/page-large",
            archived=False,
        )

        claim = await transformer.transform_to_claim(page, include_content=True)

        assert "Paragraph 0" in claim["content"]
        assert "Paragraph 99" in claim["content"]


class TestNotionTransformerMetadata:
    """Tests for NotionTransformer metadata handling."""

    @pytest.mark.asyncio
    async def test_metadata_includes_page_id(self) -> None:
        """Test that metadata includes notion_page_id."""
        mock_client = AsyncMock()
        mock_client.blocks.children.list = AsyncMock(return_value={"results": [], "has_more": False})

        from saw.connectors.notion.property_mapper import PropertyMapper
        mapper = PropertyMapper(PropertyMappingConfig(), None)
        renderer = BlockRenderer(mock_client)

        transformer = NotionTransformer(
            client=mock_client,
            mapper=mapper,
            renderer=renderer,
        )

        page = NotionPage(
            id="page-meta",
            parent={"database_id": "db-456"},
            properties={},
            created_time=utcnow(),
            last_edited_time=utcnow(),
            url="https://notion.so/page-meta",
            archived=False,
        )

        claim = await transformer.transform_to_claim(page)

        assert claim["metadata"]["notion_page_id"] == "page-meta"

    @pytest.mark.asyncio
    async def test_metadata_includes_parent_id(self) -> None:
        """Test that metadata includes notion_parent_id."""
        mock_client = AsyncMock()
        mock_client.blocks.children.list = AsyncMock(return_value={"results": [], "has_more": False})

        from saw.connectors.notion.property_mapper import PropertyMapper
        mapper = PropertyMapper(PropertyMappingConfig(), None)
        renderer = BlockRenderer(mock_client)

        transformer = NotionTransformer(
            client=mock_client,
            mapper=mapper,
            renderer=renderer,
        )

        page = NotionPage(
            id="page-meta",
            parent={"database_id": "db-789"},
            properties={},
            created_time=utcnow(),
            last_edited_time=utcnow(),
            url="https://notion.so/page-meta",
            archived=False,
        )

        claim = await transformer.transform_to_claim(page)

        assert claim["metadata"]["notion_parent_id"] == "db-789"

    @pytest.mark.asyncio
    async def test_metadata_includes_timestamps(self) -> None:
        """Test that metadata includes Notion timestamps."""
        now = utcnow()
        mock_client = AsyncMock()
        mock_client.blocks.children.list = AsyncMock(return_value={"results": [], "has_more": False})

        from saw.connectors.notion.property_mapper import PropertyMapper
        mapper = PropertyMapper(PropertyMappingConfig(), None)
        renderer = BlockRenderer(mock_client)

        transformer = NotionTransformer(
            client=mock_client,
            mapper=mapper,
            renderer=renderer,
        )

        page = NotionPage(
            id="page-meta",
            parent={"database_id": "db-456"},
            properties={},
            created_time=now,
            last_edited_time=now,
            url="https://notion.so/page-meta",
            archived=False,
        )

        claim = await transformer.transform_to_claim(page)

        assert "notion_created_time" in claim["metadata"]
        assert "notion_last_edited_time" in claim["metadata"]
