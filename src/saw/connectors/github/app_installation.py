"""GitHub App installation flow management.

Plan 14-01: GitHub connector core with OAuth/App auth.
Per GITH-01: GitHub App installation for organization-level access.
"""
from __future__ import annotations

import jwt
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from saw.connectors.token_encryption import TokenEncryption

logger = logging.getLogger(__name__)


@dataclass
class InstallationToken:
    """GitHub App installation token.

    Attributes:
        token: The installation access token.
        expires_at: Token expiration timestamp.
        repositories: List of accessible repository IDs.
        permissions: Granted permissions.
    """

    token: str
    expires_at: datetime
    repositories: list[int] = field(default_factory=list)
    permissions: dict[str, str] = field(default_factory=dict)


class GitHubAppInstallationHandler:
    """GitHub App installation flow management.

    Per GITH-01: GitHub App installation for organization-level access.

    GitHub Apps are recommended for:
    - Organization-level access
    - Fine-grained permissions
    - Higher rate limits (15000 req/hr for installations)
    """

    # Installation tokens expire after 1 hour
    TOKEN_EXPIRY_SECONDS = 3600
    # Refresh 5 minutes before expiry
    TOKEN_REFRESH_BUFFER_SECONDS = 300

    def __init__(
        self,
        app_id: str,
        private_key: str,
        encryption: TokenEncryption,
    ):
        """Initialize GitHub App installation handler.

        Args:
            app_id: GitHub App ID.
            private_key: GitHub App private key (PEM format).
            encryption: TokenEncryption instance for secure storage.
        """
        self._app_id = app_id
        self._private_key = private_key
        self._encryption = encryption
        self._installation_tokens: dict[int, InstallationToken] = {}

    @classmethod
    def from_config(
        cls,
        encryption: TokenEncryption,
    ) -> "GitHubAppInstallationHandler":
        """Create handler from environment configuration.

        Args:
            encryption: TokenEncryption instance.

        Returns:
            GitHubAppInstallationHandler instance.
        """
        import os

        app_id = os.getenv("GITHUB_APP_ID", "")
        private_key = os.getenv("GITHUB_PRIVATE_KEY", "")

        # Handle multi-line private key from env
        if private_key and "\\n" in private_key:
            private_key = private_key.replace("\\n", "\n")

        return cls(
            app_id=app_id,
            private_key=private_key,
            encryption=encryption,
        )

    def generate_jwt(self) -> str:
        """Generate JWT for GitHub App authentication.

        The JWT is used to authenticate API calls on behalf of the App,
        not on behalf of an installation.

        Returns:
            JWT string valid for 10 minutes.
        """
        now = int(time.time())

        payload = {
            # Issuer: App ID
            "iss": self._app_id,
            # Issued at: now
            "iat": now,
            # Expiration: 10 minutes from now
            "exp": now + 600,
        }

        # Sign with RSA private key
        token = jwt.encode(payload, self._private_key, algorithm="RS256")

        return token

    async def get_installations(self) -> list[dict]:
        """Get all installations for this App.

        Returns:
            List of installation dicts.
        """
        jwt_token = self.generate_jwt()

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.github.com/app/installations",
                    headers={
                        "Authorization": f"Bearer {jwt_token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get installations: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error getting installations: {e}")
            return []

    async def get_installation_token(
        self,
        installation_id: int,
        force_refresh: bool = False,
    ) -> InstallationToken:
        """Get access token for an installation.

        Installation tokens are valid for 1 hour and are cached.

        Args:
            installation_id: GitHub App installation ID.
            force_refresh: Force token refresh even if cached.

        Returns:
            InstallationToken with access token and metadata.

        Raises:
            InstallationError: If token cannot be obtained.
        """
        # Check cache
        if not force_refresh and installation_id in self._installation_tokens:
            cached = self._installation_tokens[installation_id]
            # Check if token is still valid (with buffer)
            if datetime.now(timezone.utc) < cached.expires_at - timedelta(
                seconds=self.TOKEN_REFRESH_BUFFER_SECONDS
            ):
                return cached

        jwt_token = self.generate_jwt()

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.github.com/app/installations/{installation_id}/access_tokens",
                    headers={
                        "Authorization": f"Bearer {jwt_token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                )

                if response.status_code != 201:
                    raise InstallationError(
                        f"Failed to get installation token: {response.status_code}"
                    )

                data = response.json()

                token = InstallationToken(
                    token=data["token"],
                    expires_at=datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")),
                    repositories=[r["id"] for r in data.get("repositories", [])],
                    permissions=data.get("permissions", {}),
                )

                # Cache the token
                self._installation_tokens[installation_id] = token

                return token

        except Exception as e:
            logger.error(f"Error getting installation token: {e}")
            raise InstallationError(f"Failed to get installation token: {e}")

    async def get_installation_repositories(
        self,
        installation_id: int,
    ) -> list[dict]:
        """Get repositories accessible to an installation.

        Args:
            installation_id: GitHub App installation ID.

        Returns:
            List of repository dicts.
        """
        token = await self.get_installation_token(installation_id)

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.github.com/installation/repositories",
                    headers={
                        "Authorization": f"token {token.token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("repositories", [])
                else:
                    logger.error(f"Failed to get repositories: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"Error getting repositories: {e}")
            return []

    def encrypt_token(self, token: str) -> str:
        """Encrypt token for secure storage.

        Args:
            token: Token string to encrypt.

        Returns:
            Encrypted token string.
        """
        return self._encryption.encrypt_token_set(access_token=token)

    def decrypt_token(self, encrypted: str) -> str:
        """Decrypt token from secure storage.

        Args:
            encrypted: Encrypted token string.

        Returns:
            Decrypted token string.
        """
        data = self._encryption.decrypt_token_set(encrypted)
        return data.get("access_token", "")


class InstallationError(Exception):
    """GitHub App installation error."""
    pass
