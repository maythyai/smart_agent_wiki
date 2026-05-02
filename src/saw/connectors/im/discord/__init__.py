"""Discord connector package.

Plan 13-03: Discord connector via Gateway WebSocket.
Per DISC-01~05: Bot authentication, Gateway, reconnection, embeds, rate limits.
"""
from saw.connectors.im.discord.connector import DiscordConnector
from saw.connectors.im.discord.models import DiscordMessage, DiscordUser

__all__ = [
    "DiscordConnector",
    "DiscordMessage",
    "DiscordUser",
]
