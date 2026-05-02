"""Notion page to SAW Claim transformation.

Plan 12-02: Property mapping and block transformation.
Per NOTI-03: Notion pages ingested as Claims with correct content extraction.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
import logging

from saw.connectors.notion.models import NotionPage
from saw.connectors.notion.property_mapper import PropertyMapper
from saw.connectors.notion.blocks import BlockRenderer, render_blocks_to_markdown
from saw.connectors.protocol import ConnectorItem


logger = logging.getLogger(__name__)


class NotionTransformer:
    """Transforms Notion pages to SAW Claims and vice versa.

    Per NOTI-03: Handles bidirectional conversion with content extraction.
    """

    def __init__(
        self,
        client: Any,
        mapper: PropertyMapper,
        renderer: BlockRenderer,
    ) -> None:
        """Initialize transformer.

        Args:
            client: Notion API client for fetching block children.
            mapper: PropertyMapper for property extraction.
            renderer: BlockRenderer for markdown conversion.
        """
        self._client = client
        self._mapper = mapper
        self._renderer = renderer

    async def transform_to_claim(
        self,
        page: NotionPage,
        include_content: bool = True,
    ) -> dict:
        """Transform Notion page to SAW Claim dict.

        Per NOTI-03: Extracts content from Notion blocks.

        Args:
            page: NotionPage object to transform.
            include_content: Whether to fetch and include page content.

        Returns:
            Dict matching Claim schema for SAW ingestion.
        """
        # Extract properties
        properties = dict(page.properties) if page.properties else {}

        # Map properties to SAW fields
        mapped = self._mapper.map_properties(properties)

        # Build claim dict
        claim: dict = {
            "title": mapped.get("title", ""),
            "content": "",
            "source_platform": "notion",
            "source_id": page.id,
            "source_url": page.url,
            "confidence": mapped.get("confidence", "unverified"),
            "freshness": mapped.get("freshness", "fresh"),
            "tags": mapped.get("tags", []),
            "metadata": {
                "notion_page_id": page.id,
                "notion_parent_id": page.parent.get("database_id") or page.parent.get("page_id"),
                "notion_created_time": page.created_time.isoformat() if page.created_time else None,
                "notion_last_edited_time": page.last_edited_time.isoformat() if page.last_edited_time else None,
                "notion_archived": page.archived,
                "notion_properties": properties,
            },
        }

        # Fetch and render content if requested
        if include_content:
            content = await self._fetch_page_content(page.id)
            claim["content"] = content

        return claim

    async def _fetch_page_content(self, page_id: str) -> str:
        """Fetch and render page blocks to markdown.

        Args:
            page_id: Notion page ID.

        Returns:
            Markdown-formatted content string.
        """
        try:
            blocks = []
            has_more = True
            start_cursor = None

            while has_more:
                response = await self._client.blocks.children.list(
                    block_id=page_id,
                    start_cursor=start_cursor,
                )
                blocks.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")

            # Render blocks to markdown
            return await render_blocks_to_markdown(blocks, self._renderer)

        except Exception as e:
            logger.warning(f"Failed to fetch content for page {page_id}: {e}")
            return ""

    def transform_from_claim(
        self,
        claim: dict,
        database_schema: dict,
    ) -> ConnectorItem:
        """Transform SAW Claim dict to Notion item format.

        Args:
            claim: SAW Claim dict.
            database_schema: Notion database property schema.

        Returns:
            ConnectorItem ready for Notion push.
        """
        # Map properties back to Notion format
        notion_props = self._mapper.map_to_notion_properties(claim, database_schema)

        # Build ConnectorItem
        return ConnectorItem(
            id=claim.get("source_id", ""),
            title=claim.get("title", ""),
            content=claim.get("content", ""),
            url=claim.get("source_url"),
            author=None,
            created_at=self._parse_datetime(claim.get("created_at")),
            updated_at=self._parse_datetime(claim.get("updated_at")),
            metadata={
                "notion_properties": notion_props,
                "confidence": claim.get("confidence"),
                "freshness": claim.get("freshness"),
                "tags": claim.get("tags", []),
                "database_id": claim.get("metadata", {}).get("notion_parent_id", ""),
            },
        )

    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Safely parse datetime string.

        Args:
            dt_str: ISO format datetime string.

        Returns:
            datetime or None.
        """
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
            return None
