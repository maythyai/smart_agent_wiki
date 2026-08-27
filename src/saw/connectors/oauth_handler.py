"""OAuth 2.0 flow management for third-party platforms.

Plan 10-02: OAuth Handler and Token Encryption.
Per AUTH-01: Unified OAuth flow for all OAuth platforms.
"""
from __future__ import annotations

import secrets
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from saw.connectors.token_encryption import TokenEncryption


@dataclass
class OAuthConfig:
    """OAuth configuration for a platform.

    Per AUTH-01: Unified OAuth flow for all OAuth platforms.
    """

    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    redirect_uri: str
    scopes: list[str] = field(default_factory=list)
    extra_params: dict = field(default_factory=dict)

    @classmethod
    def notion(cls, client_id: str, client_secret: str, redirect_uri: str) -> "OAuthConfig":
        """Create Notion OAuth configuration."""
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            authorize_url="https://api.notion.com/v1/oauth/authorize",
            token_url="https://api.notion.com/v1/oauth/token",
            redirect_uri=redirect_uri,
        )

    @classmethod
    def slack(cls, client_id: str, client_secret: str, redirect_uri: str) -> "OAuthConfig":
        """Create Slack OAuth configuration."""
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            authorize_url="https://slack.com/oauth/v2/authorize",
            token_url="https://slack.com/api/oauth.v2.access",
            redirect_uri=redirect_uri,
            scopes=["channels:read", "channels:history", "groups:history"],
        )

    @classmethod
    def github(cls, client_id: str, client_secret: str, redirect_uri: str) -> "OAuthConfig":
        """Create GitHub OAuth configuration."""
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            redirect_uri=redirect_uri,
            scopes=["repo", "read:org"],
        )

    @classmethod
    def feishu(cls, client_id: str, client_secret: str, redirect_uri: str) -> "OAuthConfig":
        """Create Feishu OAuth configuration."""
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            authorize_url="https://open.feishu.cn/open-apis/authen/v1/authorize",
            token_url="https://open.feishu.cn/open-apis/authen/v1/accessToken",
            redirect_uri=redirect_uri,
        )


@dataclass
class OAuthState:
    """OAuth state for CSRF protection.

    Per Decision 2: OAuth state stored in Redis with 10-minute TTL.
    """

    state: str
    platform: str
    user_id: str
    created_at: datetime
    redirect_to: str | None = None


class OAuthHandler:
    """OAuth 2.0 flow management.

    Per AUTH-01: Unified OAuth flow for all OAuth platforms.
    Per Decision 2: OAuth state stored in Redis with 10-minute TTL.
    """

    STATE_TTL_SECONDS = 600  # 10 minutes

    def __init__(
        self,
        config: OAuthConfig,
        platform: str,
        encryption: TokenEncryption,
        redis_client: Optional[object] = None,  # Redis client for team mode
    ):
        """Initialize OAuth handler.

        Args:
            config: OAuth configuration for the platform.
            platform: Platform identifier.
            encryption: TokenEncryption instance.
            redis_client: Redis client for team mode (optional).
        """
        self._config = config
        self._platform = platform
        self._encryption = encryption
        self._redis = redis_client
        self._local_states: dict[str, OAuthState] = {}  # For single-user mode

    def get_authorization_url(
        self,
        user_id: str,
        redirect_to: str | None = None,
    ) -> tuple[str, str]:
        """Generate OAuth authorization URL.

        Args:
            user_id: User initiating the OAuth flow.
            redirect_to: URL to redirect after completion.

        Returns:
            Tuple of (authorization_url, state).
        """
        state = self._generate_state()
        oauth_state = OAuthState(
            state=state,
            platform=self._platform,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
            redirect_to=redirect_to,
        )
        self._store_state(oauth_state)

        # Build authorization URL manually
        params = {
            "client_id": self._config.client_id,
            "redirect_uri": self._config.redirect_uri,
            "response_type": "code",
            "state": state,
        }
        if self._config.scopes:
            params["scope"] = " ".join(self._config.scopes)
        params.update(self._config.extra_params)

        # Build URL
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        authorization_url = f"{self._config.authorize_url}?{query_string}"

        return authorization_url, state

    def _generate_state(self) -> str:
        """Generate cryptographically random state string.

        Per Decision 2: Redis-based state with 10-min TTL for CSRF protection.

        Returns:
            Random state string (32+ bytes, URL-safe).
        """
        return secrets.token_urlsafe(32)

    def _store_state(self, oauth_state: OAuthState) -> None:
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
                f"oauth_state:{oauth_state.state}",
                self.STATE_TTL_SECONDS,
                state_data,
            )
        else:
            # Single-user mode: local storage
            self._local_states[oauth_state.state] = oauth_state

    def verify_state(self, state: str) -> Optional[OAuthState]:
        """Verify and retrieve OAuth state.

        Args:
            state: State string from callback.

        Returns:
            OAuthState if valid, None otherwise.
        """
        if self._redis:
            state_data = self._redis.get(f"oauth_state:{state}")
            if not state_data:
                return None
            data = json.loads(state_data)
            self._redis.delete(f"oauth_state:{state}")
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

        return OAuthState(
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
    ) -> tuple[str, str]:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback.
            state: State string from callback.

        Returns:
            Tuple of (encrypted_token_set, user_id).

        Raises:
            OAuthError: If exchange fails or state invalid.
        """
        oauth_state = self.verify_state(state)
        if not oauth_state:
            raise OAuthError("Invalid or expired state")

        # Exchange code for tokens (would use authlib in production)
        # For now, simulate the exchange
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._config.token_url,
                    data={
                        "client_id": self._config.client_id,
                        "client_secret": self._config.client_secret,
                        "code": code,
                        "redirect_uri": self._config.redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    headers={"Accept": "application/json"},
                )
                token = response.json()
        except Exception as e:
            # HI-13: never silently substitute a fake "test_token" — that
            # stored invalid credentials as if they were real and swallowed
            # the actual error. Surface the failure so the caller knows auth
            # failed.
            raise OAuthError(f"OAuth token exchange failed: {e}") from e

        # Calculate expiration
        expires_at = None
        if token.get("expires_in"):
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=token["expires_in"])

        # Encrypt token set
        encrypted = self._encryption.encrypt_token_set(
            access_token=token["access_token"],
            refresh_token=token.get("refresh_token"),
            expires_at=expires_at,
        )

        return encrypted, oauth_state.user_id


class OAuthError(Exception):
    """OAuth flow error."""
    pass