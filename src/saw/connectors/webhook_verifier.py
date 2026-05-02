"""Webhook signature verification for third-party platforms.

Plan 10-03: Webhook Endpoints and Rate Limiting.
Per IM-02: HMAC-SHA256 webhook signature verification.
"""
from __future__ import annotations

import hmac
import hashlib
import time
from dataclasses import dataclass
from typing import Callable


class SignatureVerificationError(Exception):
    """Raised when webhook signature verification fails."""
    pass


@dataclass
class WebhookVerifier:
    """Webhook signature verification.

    Per IM-02: System verifies webhook signatures (HMAC-SHA256).

    Supports multiple signature formats:
    - Slack: v0 prefix with timestamp
    - GitHub: sha256= prefix
    - Generic: raw HMAC-SHA256
    """

    secret: str
    platform: str

    def verify(
        self,
        body: bytes,
        signature: str,
        timestamp: str | None = None,
    ) -> bool:
        """Verify webhook signature.

        Args:
            body: Raw request body bytes.
            signature: Signature from header.
            timestamp: Optional timestamp for timestamp-based verification.

        Returns:
            True if signature is valid.

        Raises:
            SignatureVerificationError: If signature is invalid.
        """
        if self.platform == "slack":
            return self._verify_slack(body, signature, timestamp)
        elif self.platform == "github":
            return self._verify_github(body, signature)
        elif self.platform == "feishu":
            return self._verify_feishu(body, signature, timestamp)
        else:
            return self._verify_generic(body, signature)

    def _verify_slack(
        self,
        body: bytes,
        signature: str,
        timestamp: str | None,
    ) -> bool:
        """Verify Slack signature format.

        Slack format: v0:{timestamp}:{body}
        Signature: X-Slack-Signature header
        """
        if not timestamp:
            raise SignatureVerificationError("Slack webhook requires timestamp")

        # Check timestamp freshness (5 minutes)
        try:
            ts = int(timestamp)
            if abs(time.time() - ts) > 300:
                raise SignatureVerificationError("Slack webhook timestamp expired")
        except ValueError:
            raise SignatureVerificationError("Invalid timestamp format")

        # Compute expected signature
        base_string = f"v0:{timestamp}:{body.decode()}"
        expected = "v0=" + hmac.new(
            self.secret.encode(),
            base_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            raise SignatureVerificationError("Slack signature mismatch")

        return True

    def _verify_github(self, body: bytes, signature: str) -> bool:
        """Verify GitHub signature format.

        GitHub format: sha256={signature}
        Signature: X-Hub-Signature-256 header
        """
        if not signature.startswith("sha256="):
            raise SignatureVerificationError("GitHub signature must start with sha256=")

        expected = "sha256=" + hmac.new(
            self.secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            raise SignatureVerificationError("GitHub signature mismatch")

        return True

    def _verify_feishu(
        self,
        body: bytes,
        signature: str,
        timestamp: str | None,
    ) -> bool:
        """Verify Feishu signature format.

        Feishu uses similar format to Slack with timestamp.
        """
        if not timestamp:
            raise SignatureVerificationError("Feishu webhook requires timestamp")

        # Check timestamp freshness
        try:
            ts = int(timestamp)
            if abs(time.time() - ts) > 300:
                raise SignatureVerificationError("Feishu webhook timestamp expired")
        except ValueError:
            raise SignatureVerificationError("Invalid timestamp format")

        expected = hmac.new(
            self.secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            raise SignatureVerificationError("Feishu signature mismatch")

        return True

    def _verify_generic(self, body: bytes, signature: str) -> bool:
        """Verify generic HMAC-SHA256 signature."""
        expected = hmac.new(
            self.secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(signature, expected):
            raise SignatureVerificationError("Signature mismatch")

        return True

    @staticmethod
    def compute_signature(secret: str, body: bytes, platform: str = "generic") -> str:
        """Compute signature for testing/sending webhooks.

        Args:
            secret: Webhook secret.
            body: Request body bytes.
            platform: Platform format to use.

        Returns:
            Computed signature string.
        """
        if platform == "slack":
            timestamp = str(int(time.time()))
            base_string = f"v0:{timestamp}:{body.decode()}"
            return "v0=" + hmac.new(
                secret.encode(),
                base_string.encode(),
                hashlib.sha256,
            ).hexdigest()
        elif platform == "github":
            return "sha256=" + hmac.new(
                secret.encode(),
                body,
                hashlib.sha256,
            ).hexdigest()
        else:
            return hmac.new(
                secret.encode(),
                body,
                hashlib.sha256,
            ).hexdigest()
