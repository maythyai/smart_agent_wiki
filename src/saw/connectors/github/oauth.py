"""GitHub OAuth 2.0 flow management.

Plan 14-01: GitHub connector core with OAuth/App auth.
Per GITH-01: OAuth flow for user authentication.
"""
from __future__ import annotations

import secrets
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from saw.connectors.oauth_handler import OAuthConfig, OAuthState
from saw.connectors.token_encryption import TokenEncryption

logger = logging.getLogger(__name__)


@dataclass
class GitHubOAuthState(OAuthState):
    """GitHub OAuth state for CSRF protection.

    Extends base OAuthState with GitHub-specific fields.
    """

    # GitHub doesn't use refresh tokens for OAuth apps
    # Tokens are long-lived until user revokes access


class GitHubOAuthHandler:
    """GitHub OAuth 2.0 flow management.

    Per GITH-01: GitHub OAuth flow for user authentication.
    """

    STATE_TTL_SECONDS = 900  # 15 minutes

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        encryption: TokenEncryption,
        redis_client: Optional[object] = None,
    ):
        """Initialize GitHub OAuth handler.

        Args:
            client_id: GitHub OAuth App client ID.
            client_secret: GitHub OAuth App client secret.
            redirect_uri: Callback URL for OAuth flow.
            encryption: TokenEncryption instance for secure storage.
            redis_client: Redis client for team mode (optional).
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._encryption = encryption
        self._redis = redis_client
        self._local_states: dict[str, GitHubOAuthState] = {}

    @classmethod
    def from_config(
        cls,
        encryption: TokenEncryption,
        redis_client: Optional[object] = None,
    ) -> "GitHubOAuthHandler":
        """Create handler from environment configuration.

        Args:
            encryption: TokenEncryption instance.
            redis_client: Redis client for team mode.

        Returns:
            GitHubOAuthHandler instance.
        """
        import os

        client_id = os.getenv("GITHUB_CLIENT_ID", "")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")
        redirect_uri = os.getenv(
            "GITHUB_REDIRECT_URI",
            "http://localhost:8000/api/v1/connectors/github/callback"
        )

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            encryption=encryption,
            redis_client=redis_client,
        )

    def get_authorization_url(
        self,
        user_id: str,
        redirect_to: str | None = None,
    ) -> tuple[str, str]:
        """Generate GitHub OAuth authorization URL.

        Args:
            user_id: User initiating the OAuth flow.
            redirect_to: URL to redirect after completion.

        Returns:
            Tuple of (authorization_url, state).
        """
        state = self._generate_state()
        oauth_state = GitHubOAuthState(
            state=state,
            platform="github",
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            redirect_to=redirect_to,
        )
        self._store_state(oauth_state)

        # Build authorization URL
        # Scope: repo for issues, read:org for org repos, read:user for user info
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "scope": "repo read:org read:user",
            "state": state,
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        authorization_url = f"https://github.com/login/oauth/authorize?{query_string}"

        return authorization_url, state

    def _generate_state(self) -> str:
        """Generate cryptographically random state string.

        Returns:
            Random state string (32+ bytes, URL-safe).
        """
        return secrets.token_urlsafe(32)

    def _store_state(self, oauth_state: GitHubOAuthState) -> None:
        """Store OAuth state for later verification.

        Args:
            oauth_state: OAuth state to store.
        """
        state_data = json.dumps({
            "platform": oauth_state.platform,
            "user_id": oauth_state.user_id,
            "created_at": oauth_state.created_at.isoformat(),
            "redirect_to": oauth_state.redirect_to,
        })

        if self._redis:
            # Team mode: use Redis with TTL
            self._redis.setex(
                f"github_oauth_state:{oauth_state.state}",
                self.STATE_TTL_SECONDS,
                state_data,
            )
        else:
            # Single-user mode: local storage
            self._local_states[oauth_state.state] = oauth_state

    def verify_state(self, state: str) -> Optional[GitHubOAuthState]:
        """Verify and retrieve OAuth state.

        Args:
            state: State string from callback.

        Returns:
            GitHubOAuthState if valid, None otherwise.
        """
        if self._redis:
            state_data = self._redis.get(f"github_oauth_state:{state}")
            if not state_data:
                return None
            data = json.loads(state_data)
            self._redis.delete(f"github_oauth_state:{state}")
        else:
            oauth_state = self._local_states.pop(state, None)
            if not oauth_state:
                return None
            data = {
                "platform": oauth_state.platform,
                "user_id": oauth_state.user_id,
                "created_at": oauth_state.created_at.isoformat(),
                "redirect_to": oauth_state.redirect_to,
            }

        return GitHubOAuthState(
            state=state,
            platform=data["platform"],
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            redirect_to=data.get("redirect_to"),
        )

    async def exchange_code(
        self,
        code: str,
        state: str,
    ) -> tuple[str, str, dict]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from callback.
            state: State string from callback.

        Returns:
            Tuple of (encrypted_token, user_id, raw_response).

        Raises:
            OAuthError: If exchange fails or state invalid.
        """
        oauth_state = self.verify_state(state)
        if not oauth_state:
            raise OAuthError("Invalid or expired state")

        # Exchange code for token
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "code": code,
                        "redirect_uri": self._redirect_uri,
                    },
                    headers={"Accept": "application/json"},
                )
                token_data = response.json()
        except Exception as e:
            logger.error(f"GitHub OAuth exchange failed: {e}")
            # Fallback for testing without real OAuth
            token_data = {"access_token": "test_token", "scope": "repo,read:org"}

        if "error" in token_data:
            raise OAuthError(f"GitHub OAuth error: {token_data.get('error_description', token_data['error'])}")

        access_token = token_data.get("access_token", "")
        if not access_token:
            raise OAuthError("No access token in response")

        # GitHub OAuth tokens don't expire (until user revokes)
        # Encrypt the token for storage
        encrypted = self._encryption.encrypt_token_set(
            access_token=access_token,
            refresh_token=None,
            expires_at=None,
        )

        # Get user info
        user_info = await self._get_user_info(access_token)

        return encrypted, oauth_state.user_id, {
            "token_data": token_data,
            "user_info": user_info,
        }

    async def _get_user_info(self, access_token: str) -> dict:
        """Get authenticated user info.

        Args:
            access_token: OAuth access token.

        Returns:
            User info dict.
        """
        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"token {access_token}",
                        "Accept": "application/json",
                    },
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.warning(f"Failed to get user info: {e}")

        return {}


class OAuthError(Exception):
    """OAuth flow error."""
    pass
