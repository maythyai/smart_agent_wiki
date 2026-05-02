"""Slack connector package.

Plan 13-02: Slack connector for message ingestion.
Per SLAK-01~06: OAuth, Events API, message handling, rate limits.
"""
from saw.connectors.im.slack.connector import SlackConnector
from saw.connectors.im.slack.models import SlackMessage, SlackUser
from saw.connectors.im.slack.oauth import SlackOAuthHandler
from saw.connectors.im.slack.event_handler import SlackEventHandler

__all__ = [
    "SlackConnector",
    "SlackMessage",
    "SlackUser",
    "SlackOAuthHandler",
    "SlackEventHandler",
]
