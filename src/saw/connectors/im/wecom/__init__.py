"""WeCom (企业微信) connector package.

Plan 13-04: WeCom connector for webhook message ingestion.
Per WECO-01~04: Webhook URL, encryption, rate limits.
"""
from saw.connectors.im.wecom.connector import WeComConnector
from saw.connectors.im.wecom.models import WeComMessage
from saw.connectors.im.wecom.crypto import WeComCrypto

__all__ = [
    "WeComConnector",
    "WeComMessage",
    "WeComCrypto",
]