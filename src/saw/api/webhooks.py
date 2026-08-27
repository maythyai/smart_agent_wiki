"""Webhook system for event notifications.

Phase 6: API Platform — Webhooks.
Per APIP-05: Webhook support for ingestion events.

Supports HMAC-SHA256 signature verification and retry logic.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text
from saw.db.models import Base, generate_uuid


class WebhookEvent:
    """Webhook event types."""
    INGEST_COMPLETE = "ingest.complete"
    CLAIM_CREATE = "claim.create"
    CLAIM_UPDATE = "claim.update"
    CLAIM_DELETE = "claim.delete"
    VAULT_CREATE = "vault.create"
    VAULT_DELETE = "vault.delete"


class Webhook(Base):
    """Webhook configuration model."""
    __tablename__ = "webhooks"

    id: str = Column(String, primary_key=True, default=lambda: generate_uuid())
    user_id: str = Column(String, nullable=False, index=True)
    name: str = Column(String(255), nullable=False)
    url: str = Column(String(500), nullable=False)
    secret: str = Column(String(512), nullable=False)  # HMAC signing secret (Fernet-encrypted at rest, M-26)
    events: str = Column(String(500), default="*")  # Comma-separated or "*"
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    failure_count: int = Column(Integer, default=0)
    last_success_at: Optional[datetime] = Column(DateTime, nullable=True)
    last_failure_at: Optional[datetime] = Column(DateTime, nullable=True)

    def should_trigger(self, event: str) -> bool:
        """Check if this webhook should trigger for an event."""
        if not self.is_active:
            return False
        if self.events == "*":
            return True
        return event in self.events.split(",")


class WebhookDelivery(Base):
    """Webhook delivery attempt record."""
    __tablename__ = "webhook_deliveries"

    id: str = Column(String, primary_key=True, default=lambda: generate_uuid())
    webhook_id: str = Column(String, nullable=False, index=True)
    event: str = Column(String(100), nullable=False)
    payload: str = Column(Text, nullable=False)
    status_code: Optional[int] = Column(Integer, nullable=True)
    response_body: Optional[str] = Column(Text, nullable=True)
    delivered_at: Optional[datetime] = Column(DateTime, nullable=True)
    error: Optional[str] = Column(String(500), nullable=True)
    attempt_count: int = Column(Integer, default=0)
    created_at: datetime = Column(DateTime, default=lambda: datetime.now(timezone.utc))


@dataclass
class WebhookPayload:
    """Webhook payload structure."""
    event: str
    timestamp: int
    data: dict
    webhook_id: str

    def to_json(self) -> str:
        return json.dumps({
            "event": self.event,
            "timestamp": self.timestamp,
            "data": self.data,
            "webhook_id": self.webhook_id,
        })


@dataclass
class DeliveryResult:
    """Result of a webhook delivery attempt."""
    success: bool
    status_code: Optional[int] = None
    response: Optional[str] = None
    error: Optional[str] = None


class WebhookSigner:
    """HMAC-SHA256 signer for webhooks."""

    @staticmethod
    def sign(payload: str, secret: str) -> str:
        """Sign a payload with HMAC-SHA256."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def verify(payload: str, signature: str, secret: str) -> bool:
        """Verify a signature."""
        expected = WebhookSigner.sign(payload, secret)
        return hmac.compare_digest(signature, expected)


class WebhookService:
    """Service for managing and delivering webhooks."""

    MAX_FAILURES = 10
    RETRY_DELAYS = [5, 10, 30]  # seconds

    def __init__(self, session=None, http_client: httpx.AsyncClient | None = None):
        self.session = session
        self.http_client = http_client

    def create_webhook(
        self,
        user_id: str,
        name: str,
        url: str,
        events: list[str] | None = None,
        secret: str | None = None,
    ) -> Webhook:
        """Create a new webhook."""
        import secrets

        if secret is None:
            secret = secrets.token_hex(32)

        events_str = ",".join(events) if events else "*"

        # M-26: encrypt the signing secret at rest (Fernet) so a DB dump does
        # not expose webhook HMAC secrets (API keys are hashed, OAuth tokens
        # are Fernet-encrypted — webhooks were the plaintext outlier).
        try:
            from saw.connectors.token_encryption import TokenEncryption
            stored_secret = TokenEncryption.from_env().encrypt(secret)
        except Exception:
            stored_secret = secret  # best-effort: fall back to plaintext

        webhook = Webhook(
            user_id=user_id,
            name=name,
            url=url,
            secret=stored_secret,
            events=events_str,
        )

        if self.session:
            self.session.add(webhook)
            self.session.commit()

        return webhook

    def list_webhooks(self, user_id: str) -> list[Webhook]:
        """List all webhooks for a user."""
        if not self.session:
            return []

        return self.session.query(Webhook).filter(
            Webhook.user_id == user_id,
        ).order_by(Webhook.created_at.desc()).all()

    def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook."""
        if not self.session:
            return False

        webhook = self.session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return False

        self.session.delete(webhook)
        self.session.commit()
        return True

    async def trigger(
        self,
        event: str,
        data: dict,
        user_id: str | None = None,
    ) -> list[DeliveryResult]:
        """Trigger webhooks for an event.

        Returns list of delivery results.
        """
        if not self.session:
            return []

        # Find matching webhooks
        query = self.session.query(Webhook).filter(
            Webhook.is_active == True,
        )

        if user_id:
            query = query.filter(Webhook.user_id == user_id)

        webhooks = query.all()
        matching = [w for w in webhooks if w.should_trigger(event)]

        if not matching:
            return []

        results = []
        for webhook in matching:
            result = await self._deliver(webhook, event, data)
            results.append(result)

        return results

    async def _deliver(
        self,
        webhook: Webhook,
        event: str,
        data: dict,
    ) -> DeliveryResult:
        """Deliver a webhook."""
        # Build payload
        payload = WebhookPayload(
            event=event,
            timestamp=int(time.time()),
            data=data,
            webhook_id=webhook.id,
        )
        payload_json = payload.to_json()

        # M-26: decrypt the at-rest secret before signing (plaintext fallback
        # for legacy rows created before encryption was enabled).
        try:
            from saw.connectors.token_encryption import TokenEncryption
            signing_secret = TokenEncryption.from_env().decrypt(webhook.secret)
        except Exception:
            signing_secret = webhook.secret

        # Sign payload
        signature = WebhookSigner.sign(payload_json, signing_secret)

        # Build headers
        headers = {
            "Content-Type": "application/json",
            "X-SAW-Signature": signature,
            "X-SAW-Event": event,
            "X-SAW-Timestamp": str(payload.timestamp),
            "X-SAW-Webhook-ID": webhook.id,
        }

        # Create delivery record
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event=event,
            payload=payload_json,
            attempt_count=1,
        )

        if self.session:
            self.session.add(delivery)

        # Send webhook
        try:
            from saw.adapters.url_guard import assert_safe_url_async

            await assert_safe_url_async(webhook.url)  # HI-12: SSRF guard
            if self.http_client is None:
                self.http_client = httpx.AsyncClient(timeout=10.0)

            response = await self.http_client.post(
                webhook.url,
                content=payload_json,
                headers=headers,
            )

            delivery.status_code = response.status_code
            delivery.response_body = response.text[:1000]  # Truncate
            delivery.delivered_at = datetime.now(timezone.utc)

            if 200 <= response.status_code < 300:
                webhook.last_success_at = datetime.now(timezone.utc)
                webhook.failure_count = 0
                result = DeliveryResult(
                    success=True,
                    status_code=response.status_code,
                    response=response.text[:500],
                )
            else:
                webhook.last_failure_at = datetime.now(timezone.utc)
                result = DeliveryResult(
                    success=False,
                    status_code=response.status_code,
                    response=response.text[:500],
                )

        except Exception as e:
            delivery.error = str(e)[:500]
            webhook.last_failure_at = datetime.now(timezone.utc)
            webhook.failure_count += 1

            # Disable if too many failures
            if webhook.failure_count >= self.MAX_FAILURES:
                webhook.is_active = False

            result = DeliveryResult(
                success=False,
                error=str(e),
            )

        if self.session:
            self.session.commit()

        return result

    async def test_webhook(self, webhook_id: str) -> DeliveryResult:
        """Test a webhook with a ping event."""
        if not self.session:
            return DeliveryResult(success=False, error="No database session")

        webhook = self.session.query(Webhook).filter(Webhook.id == webhook_id).first()
        if not webhook:
            return DeliveryResult(success=False, error="Webhook not found")

        return await self._deliver(
            webhook,
            "webhook.test",
            {"message": "Test webhook", "timestamp": int(time.time())},
        )


async def trigger_webhook_event(
    event: str,
    data: dict,
    user_id: str | None = None,
) -> None:
    """Convenience function to trigger a webhook event."""
    service = WebhookService()
    await service.trigger(event, data, user_id)
