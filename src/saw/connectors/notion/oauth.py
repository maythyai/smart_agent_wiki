"""Notion-specific OAuth handler.

Plan 12-01: Notion connector core with OAuth.
Per NOTI-01: OAuth workspace connection.
"""
from __future__ import annotations

from typing import Optional

from saw.connectors.oauth_handler import OAuthHandler, OAuthConfig, OAuthError
from saw.connectors.token_encryption import TokenEncryption


class NotionOAuthHandler:
    """Notion-specific OAuth handling.

    Per NOTI-01: Notion OAuth returns workspace_id and workspace_name in token response.
    """

    def __init__(
        self,
        config: OAuthConfig,
        encryption: TokenEncryption,
        redis_client: Optional[object] = None,
    ) -> None:
        """Initialize Notion OAuth handler.

        Args:
            config: OAuth configuration for Notion.
            encryption: TokenEncryption instance.
            redis_client: Redis client for team mode (optional).
        """
        self._handler = OAuthHandler(
            config=config,
            platform="notion",
            encryption=encryption,
            redis_client=redis_client,
        )
        self._config = config

    def get_authorization_url(
        self,
        user_id: str,
        redirect_to: str | None = None,
    ) -> tuple[str, str]:
        """Generate Notion OAuth authorization URL.

        Args:
            user_id: User initiating the OAuth flow.
            redirect_to: URL to redirect after completion.

        Returns:
            Tuple of (authorization_url, state).
        """
        return self._handler.get_authorization_url(user_id, redirect_to)

    async def exchange_code(
        self,
        code: str,
        state: str,
    ) -> tuple[dict, str]:
        """Exchange authorization code for tokens.

        Notion-specific response parsing for workspace info.

        Args:
            code: Authorization code from callback.
            state: State string from callback.

        Returns:
            Tuple of (token_response_dict, user_id).

        Raises:
            OAuthError: If exchange fails or state invalid.
        """
        # Verify state
        oauth_state = self._handler.verify_state(state)
        if not oauth_state:
            raise OAuthError("Invalid or expired state")

        # Exchange code with Notion
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._config.token_url,
                    json={
                        "client_id": self._config.client_id,
                        "client_secret": self._config.client_secret,
                        "code": code,
                        "redirect_uri": self._config.redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    headers={"Content-Type": "application/json"},
                )
                token = response.json()
        except Exception as e:
            raise OAuthError(f"Token exchange failed: {str(e)}")

        # Handle Notion OAuth errors
        if "error" in token:
            raise OAuthError(f"Notion OAuth error: {token['error']}")

        # Extract workspace info from Notion response
        # Notion returns: access_token, workspace_id, workspace_name, bot_id
        workspace_id = token.get("workspace_id", "")
        workspace_name = token.get("workspace_name", "")

        # Encrypt and return
        encrypted = self._handler._encryption.encrypt_token_set(
            access_token=token.get("access_token", ""),
            refresh_token=token.get("refresh_token"),
            expires_at=None,  # Notion tokens don't expire typically
        )

        return {
            "encrypted_token": encrypted,
            "workspace_id": workspace_id,
            "workspace_name": workspace_name,
            "bot_id": token.get("bot_id", ""),
            "raw_response": token,
        }, oauth_state.user_id

    def verify_state(self, state: str) -> Optional[dict]:
        """Verify OAuth state.

        Args:
            state: State string from callback.

        Returns:
            State data if valid, None otherwise.
        """
        oauth_state = self._handler.verify_state(state)
        if oauth_state:
            return {
                "platform": oauth_state.platform,
                "user_id": oauth_state.user_id,
                "created_at": oauth_state.created_at,
                "redirect_to": oauth_state.redirect_to,
            }
        return None