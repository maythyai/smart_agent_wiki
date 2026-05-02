"""WeCom connector models.

Plan 13-04 Task 4: WeCom message model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any


@dataclass
class WeComMessage:
    """WeCom message model.

    WeCom sends messages via webhook in XML format.

    Attributes:
        message_id: Message ID.
        from_user: Sender user ID.
        to_user: Receiver user ID (bot).
        content: Message content.
        message_type: Message type (text, image, etc).
        timestamp: Message timestamp.
        chat_id: Group chat ID if in group.
    """

    message_id: str
    from_user: str
    to_user: str
    content: str
    message_type: str = "text"
    timestamp: Optional[datetime] = None
    chat_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_xml(cls, xml_data: dict) -> "WeComMessage":
        """Create from WeCom XML webhook data.

        WeCom sends webhook data as XML.
        """
        xml_msg = xml_data.get("xml", xml_data)

        # Parse timestamp
        timestamp = None
        ts = xml_msg.get("CreateTime")
        if ts:
            try:
                timestamp = datetime.fromtimestamp(int(ts), tz=None)
            except ValueError:
                pass

        return cls(
            message_id=xml_msg.get("MsgId", ""),
            from_user=xml_msg.get("FromUserName", ""),
            to_user=xml_msg.get("ToUserName", ""),
            content=cls._decode_content(xml_msg.get("Content", "")),
            message_type=xml_msg.get("MsgType", "text"),
            timestamp=timestamp,
            chat_id=xml_msg.get("ChatId"),
            metadata={
                "agent_id": xml_msg.get("AgentID"),
                "msg_type": xml_msg.get("MsgType"),
            },
        )

    @staticmethod
    def _decode_content(content: str) -> str:
        """Decode content, handling Chinese encoding."""
        # WeCom typically sends UTF-8 encoded content
        return content

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "message_id": self.message_id,
            "from_user": self.from_user,
            "to_user": self.to_user,
            "content": self.content,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "chat_id": self.chat_id,
            "metadata": self.metadata,
        }