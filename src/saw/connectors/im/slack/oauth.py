"""Slack OAuth 2.0 handler.

Plan 13-02 Task 2: Slack OAuth flow.
Per SLAK-01: Install Slack app via OAuth 2.0.
"""
from __future__ import annotations

import httpx
from urllib.parse import urlencode
from typing import Optional

from saw.connectors.protocol import AuthResult


# Required OAuth scopes for message ingestion
SLACK_SCOPES = [
    "channels:history",  # Read messages in public channels
    "channels:read",     # List public channels
    "groups:history",    # Read messages in private channels
    "groups:read",       # List private channels
    "im:history",        # Read direct messages
    "im:read",           # List direct messages
    "users:read",        # Get user info
]


class SlackOAuthHandler:
    """Handle Slack OAuth 2.0 flow.

    Per SLAK-01: Install Slack app via OAuth 2.0.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> None:
        """Initialize OAuth handler.

        Args:
            client_id: Slack app client ID.
            client_secret: Slack app client secret.
            redirect_uri: OAuth redirect URI.
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def get_authorize_url(self, state: str) -> str:
        """Generate OAuth authorization URL.

        Args:
            state: CSRF protection state token.

        Returns:
            Full authorization URL.
        """
        params = {
            "client_id": self._client_id,
            "scope": ",".join(SLACK_SCOPES),
            "state": state,
            "redirect_uri": self._redirect_uri,
        }
        return f"https://slack.com/oauth/v2/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str) -> AuthResult:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback.

        Returns:
            AuthResult with tokens and team info.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/oauth.v2.access",
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "code": code,
                    "redirect_uri": self._redirect_uri,
                },
            )
            data = response.json()

        if not data.get("ok"):
            return AuthResult(
                access_token="",
                raw_response={"error": data.get("error", "Unknown error")},
            )

        return AuthResult(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            scopes=data.get("scope", "").split(","),
            raw_response={
                "bot_token": data.get("access_token"),
                "user_token": data.get("authed_user", {}).get("access_token"),
                "team_id": data.get("team", {}).get("id"),
                "team_name": data.get("team", {}).get("name"),
                "bot_user_id": data.get("bot_user_id"),
            },
        )

    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """Refresh expired token.

        Note: Slack doesn't use refresh tokens for bot tokens.
        Bot tokens are long-lived.
        """
        # Slack bot tokens don't expire, no refresh needed
        return AuthResult(
            access_token="",
            raw_response={"error": "Slack bot tokens do not expire"},
        )
