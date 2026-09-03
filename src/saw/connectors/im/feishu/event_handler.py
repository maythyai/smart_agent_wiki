"""Feishu event handler.

Plan 13-04 Task 3: Process Feishu webhook events.
Per FEIS-02: Receive messages via Feishu webhook events.
Per FEIS-04: Capture Feishu Wiki docs as content source.
Per FEIS-05: Handle Chinese content encoding.
"""
from __future__ import annotations

import logging
from typing import Callable, Optional

from saw.connectors.im.feishu.models import FeishuMessage
from saw.connectors.protocol import ConnectorItem

logger = logging.getLogger(__name__)


class FeishuEventHandler:
    """Handle Feishu webhook events.

    Per FEIS-02: Receive messages via Feishu webhook events.
    Per FEIS-04: Capture Feishu Wiki docs as content source.
    """

    _instance: Optional["FeishuEventHandler"] = None

    def __init__(self) -> None:
        """Initialize event handler."""
        self._item_callback: Optional[Callable[[ConnectorItem], None]] = None

    @classmethod
    def get_instance(cls) -> "FeishuEventHandler":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_item_callback(self, callback: Callable[[ConnectorItem], None]) -> None:
        """Set callback for processed items."""
        self._item_callback = callback

    async def process_event(self, event_data: dict) -> list[ConnectorItem]:
        """Process Feishu event and return items.

        Per FEIS-02: Process webhook events.
        """
        header = event_data.get("header", {})
        event_type = header.get("event_type", "")

        if event_type == "im.message.receive_v1":
            return await self._process_message_event(event_data)
        elif event_type == "drive.file.created_v1":
            return await self._process_wiki_doc_event(event_data)

        return []

    async def _process_message_event(self, event_data: dict) -> list[ConnectorItem]:
        """Process message event.

        Per FEIS-05: Handle Chinese content encoding.
        """
        event = event_data.get("event", {})

        feishu_message = FeishuMessage.from_event(event)

        # Convert to ConnectorItem
        item = ConnectorItem(
            id=f"feishu-{feishu_message.chat_id}-{feishu_message.message_id}",
            title=f"Feishu message in {feishu_message.chat_id}",
            content=feishu_message.content,
            url=self._build_permalink(feishu_message),
            author=feishu_message.author.name,
            created_at=feishu_message.created_at,
            metadata={
                "platform": "feishu",
                "chat_id": feishu_message.chat_id,
                "author": feishu_message.author.to_dict(),
                "message_type": feishu_message.message_type,
                "chat_type": feishu_message.metadata.get("chat_type"),
                "parent_message_id": feishu_message.metadata.get("parent_message_id"),
            },
        )

        if self._item_callback:
            self._item_callback(item)

        return [item]

    async def _process_wiki_doc_event(self, event_data: dict) -> list[ConnectorItem]:
        """Process wiki doc creation event.

        Per FEIS-04: Capture Feishu Wiki docs as content source.
        """
        event = event_data.get("event", {})
        file_info = event.get("file", {})

        item = ConnectorItem(
            id=f"feishu-doc-{file_info.get('token', 'unknown')}",
            title=file_info.get("name", "Wiki Document"),
            content="",  # Would need to fetch content separately
            url=file_info.get("url"),
            author=None,
            metadata={
                "platform": "feishu",
                "type": "wiki_doc",
                "doc_token": file_info.get("token"),
                "space_id": event.get("space", {}).get("space_id"),
                "created_time": event.get("created_time"),
            },
        )

        return [item]

    def _build_permalink(self, message: FeishuMessage) -> Optional[str]:
        """Build permalink to original message."""
        # Feishu doesn't have simple permalink URLs
        return None