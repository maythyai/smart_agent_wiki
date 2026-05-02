"""Webhook logging with token masking for audit trail.

Plan 10-03: Webhook Endpoints and Rate Limiting.
Per AUTH-04: Tokens masked in logs and API responses.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from saw.connectors.models import TokenMasker


# Token fields to mask in webhook payloads
SENSITIVE_FIELDS = [
    "access_token",
    "refresh_token",
    "token",
    "authorization",
    "api_key",
    "secret",
]


@dataclass
class WebhookLogEntry:
    """Webhook event log entry."""
    id: str
    platform: str
    event_type: str
    event_id: str
    payload_masked: dict
    received_at: datetime
    processed_at: datetime | None = None
    status: str = "received"  # received, processed, failed
    error_message: str | None = None
    rate_limit_remaining: int | None = None
    connector_id: str | None = None


class WebhookLogger:
    """Logger for webhook events with token masking.

    Per AUTH-04: Tokens masked in logs and API responses.
    """

    def __init__(self, db_session: Session):
        """Initialize webhook logger.

        Args:
            db_session: SQLAlchemy database session.
        """
        self._db = db_session
        self._masker = TokenMasker()

    def log_received(
        self,
        platform: str,
        event_type: str,
        event_id: str,
        payload: dict,
        rate_limit_remaining: int | None = None,
        connector_id: str | None = None,
    ) -> str:
        """Log a received webhook event.

        Args:
            platform: Platform identifier.
            event_type: Event type from webhook.
            event_id: Event ID from platform.
            payload: Webhook payload (will be masked).
            rate_limit_remaining: Remaining rate limit.
            connector_id: Connector that received webhook.

        Returns:
            Log entry ID.
        """
        log_id = str(uuid.uuid4())

        # Mask sensitive fields
        masked_payload = self._mask_payload(payload)

        # Create log entry
        log_entry = WebhookLogEntry(
            id=log_id,
            platform=platform,
            event_type=event_type,
            event_id=event_id,
            payload_masked=masked_payload,
            received_at=datetime.now(timezone.utc),
            rate_limit_remaining=rate_limit_remaining,
            connector_id=connector_id,
        )

        # Store in database (using ConnectorSyncLog from Plan 10-01)
        from saw.db.connector_models import ConnectorSyncLog

        sync_log = ConnectorSyncLog(
            id=log_id,
            config_id=connector_id or "unknown",
            direction="webhook",
            items_pulled=1,
            items_pushed=0,
            conflicts_detected=0,
            errors=None,
            started_at=log_entry.received_at,
            completed_at=None,
            duration_ms=None,
        )
        self._db.add(sync_log)
        self._db.commit()

        return log_id

    def mark_processed(self, log_id: str) -> None:
        """Mark webhook as successfully processed.

        Args:
            log_id: Log entry ID.
        """
        from saw.db.connector_models import ConnectorSyncLog

        # Update log entry
        log_entry = self._db.query(ConnectorSyncLog).filter(
            ConnectorSyncLog.id == log_id
        ).first()
        if log_entry:
            log_entry.completed_at = datetime.now(timezone.utc)
            self._db.commit()

    def mark_failed(self, log_id: str, error: str) -> None:
        """Mark webhook as failed.

        Args:
            log_id: Log entry ID.
            error: Error message.
        """
        from saw.db.connector_models import ConnectorSyncLog

        log_entry = self._db.query(ConnectorSyncLog).filter(
            ConnectorSyncLog.id == log_id
        ).first()
        if log_entry:
            log_entry.completed_at = datetime.now(timezone.utc)
            log_entry.errors = json.dumps([error])
            self._db.commit()

    def get_failed_webhooks(
        self,
        platform: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """Get failed webhooks for retry.

        Args:
            platform: Filter by platform (optional).
            since: Filter by date (optional).
            limit: Maximum results.

        Returns:
            List of failed webhook entries.
        """
        from saw.db.connector_models import ConnectorSyncLog

        query = self._db.query(ConnectorSyncLog).filter(
            ConnectorSyncLog.direction == "webhook",
            ConnectorSyncLog.errors.isnot(None),
        )

        if platform:
            query = query.filter(ConnectorSyncLog.config_id.contains(platform))
        if since:
            query = query.filter(ConnectorSyncLog.started_at >= since)

        results = query.order_by(desc(ConnectorSyncLog.started_at)).limit(limit).all()

        return [
            {
                "id": r.id,
                "config_id": r.config_id,
                "error": r.errors,
                "started_at": r.started_at.isoformat(),
            }
            for r in results
        ]

    def _mask_payload(self, payload: dict) -> dict:
        """Recursively mask sensitive fields in payload.

        Args:
            payload: Original payload dict.

        Returns:
            Payload with sensitive fields masked.
        """
        return self._mask_dict_recursive(payload)

    def _mask_dict_recursive(self, d: dict) -> dict:
        """Recursively mask sensitive fields in dictionary.

        Args:
            d: Dictionary to mask.

        Returns:
            Copy of dict with sensitive fields masked.
        """
        result = {}
        for key, value in d.items():
            key_lower = key.lower()

            # Check if this is a sensitive key
            is_sensitive = any(
                sensitive in key_lower for sensitive in SENSITIVE_FIELDS
            )

            if is_sensitive and isinstance(value, str):
                result[key] = self._masker.mask_token(value)
            elif isinstance(value, dict):
                result[key] = self._mask_dict_recursive(value)
            elif isinstance(value, list):
                result[key] = [
                    self._mask_dict_recursive(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value

        return result
