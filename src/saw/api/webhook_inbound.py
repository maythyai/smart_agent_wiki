"""FastAPI endpoints for unified inbound webhook handling.

Plan 10-03: Webhook Endpoints and Rate Limiting.
Per IM-01: Unified webhook endpoint `/api/v1/webhooks/{platform}`.
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Any, Optional

from saw.connectors.webhook_verifier import WebhookVerifier, SignatureVerificationError
from saw.connectors.rate_limiter import WebhookRateLimiter
from saw.connectors.models import TokenMasker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks-inbound"])


class WebhookEvent(BaseModel):
    """Webhook event data."""
    platform: str
    event_type: str
    payload: dict
    received_at: datetime
    connector_id: str | None = None


class WebhookResponse(BaseModel):
    """Response for webhook receipt."""
    status: str
    platform: str
    event_id: str


class PlatformInfo(BaseModel):
    """Platform information for webhooks."""
    name: str
    display_name: str
    signature_header: str
    timestamp_header: str | None = None


# Platform-specific header configuration
SIGNATURE_HEADERS = {
    "slack": "X-Slack-Signature",
    "github": "X-Hub-Signature-256",
    "discord": "X-Signature-Ed25519",
    "feishu": "X-Lark-Signature",
}

TIMESTAMP_HEADERS = {
    "slack": "X-Slack-Request-Timestamp",
    "discord": "X-Signature-Timestamp",
    "feishu": "X-Lark-Request-Timestamp",
}


@router.get("/platforms", response_model=list[PlatformInfo])
async def list_webhook_platforms():
    """List supported webhook platforms.

    Returns:
        List of supported platforms with signature header info.
    """
    return [
        PlatformInfo(
            name="slack",
            display_name="Slack",
            signature_header="X-Slack-Signature",
            timestamp_header="X-Slack-Request-Timestamp",
        ),
        PlatformInfo(
            name="github",
            display_name="GitHub",
            signature_header="X-Hub-Signature-256",
            timestamp_header=None,
        ),
        PlatformInfo(
            name="discord",
            display_name="Discord",
            signature_header="X-Signature-Ed25519",
            timestamp_header="X-Signature-Timestamp",
        ),
        PlatformInfo(
            name="feishu",
            display_name="Feishu",
            signature_header="X-Lark-Signature",
            timestamp_header="X-Lark-Request-Timestamp",
        ),
    ]


@router.post("/{platform}")
async def receive_webhook(
    platform: str,
    request: Request,
):
    """Receive webhook from external platform.

    Per IM-01: Unified webhook endpoint `/api/v1/webhooks/{platform}`.
    Per IM-02: System verifies webhook signatures (HMAC-SHA256).

    Args:
        platform: Platform identifier (slack, github, discord, feishu).
        request: FastAPI request.

    Returns:
        JSON response with event status.

    Raises:
        400: Invalid signature or payload.
        404: Unknown platform.
        429: Rate limit exceeded.
    """
    # Check platform is supported
    supported_platforms = ["slack", "github", "discord", "feishu"]
    if platform not in supported_platforms:
        raise HTTPException(404, f"Unknown platform: {platform}")

    # Rate limiting
    rate_limiter = WebhookRateLimiter(platform)
    allowed, headers = await rate_limiter.acquire()

    if not allowed:
        logger.warning(f"Webhook rate limit exceeded for {platform}")
        raise HTTPException(
            429,
            "Rate limit exceeded",
            headers=headers,
        )

    # Get request body
    body = await request.body()

    # Get signature header (platform-specific)
    signature_header = SIGNATURE_HEADERS.get(platform, "")
    signature = request.headers.get(signature_header, "")

    # Get timestamp header (platform-specific)
    timestamp_header = TIMESTAMP_HEADERS.get(platform)
    timestamp = request.headers.get(timestamp_header, "") if timestamp_header else None

    # Get webhook secret from configuration
    secret = _get_webhook_secret(platform, request)

    if not secret:
        logger.error(f"No webhook secret configured for {platform}")
        raise HTTPException(500, f"Platform {platform} not configured")

    # Verify signature
    verifier = WebhookVerifier(secret=secret, platform=platform)

    try:
        verifier.verify(body, signature, timestamp)
    except SignatureVerificationError as e:
        logger.warning(
            f"Webhook signature verification failed for {platform}: {e}"
        )
        raise HTTPException(400, f"Invalid signature: {e}")

    # Parse webhook payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON payload")

    # Log webhook receipt (with masked tokens per AUTH-04)
    event_id = payload.get("event_id", "unknown")
    event_type = payload.get("type", payload.get("event_type", "unknown"))

    logger.info(
        f"Webhook received: platform={platform}, type={event_type}, event_id={event_id}"
    )

    webhook_event = WebhookEvent(
        platform=platform,
        event_type=event_type,
        payload=payload,
        received_at=datetime.now(timezone.utc),
    )

    # F-CONN-06: process the verified webhook into a claim via the Write
    # Queue. Previously the endpoint only acknowledged receipt, so push-based
    # intake was a dead end — verified webhook content never reached the KB.
    write_queue = getattr(request.app.state, "write_queue", None)
    if write_queue is not None:
        try:
            content = _extract_text(platform, payload)
            if content:
                from saw.write_queue.queue import WriteOp
                from saw.domain.value_objects import WriteOpStatus

                op = WriteOp(
                    op_id=f"webhook-{platform}-{event_id}",
                    session_id=f"webhook-{platform}",
                    sink_name="claims",
                    payload={
                        "content": content,
                        "source_platform": platform,
                        "source_id": str(event_id),
                        "source_url": payload.get("event_url") or payload.get("url"),
                    },
                    status=WriteOpStatus.PENDING,
                )
                write_queue.enqueue([op])
        except Exception as e:
            logger.warning("Failed to enqueue webhook claim for %s: %s", platform, e)

    return JSONResponse(
        status_code=200,
        content={
            "status": "received",
            "platform": platform,
            "event_id": event_id,
        },
        headers=headers,
    )


def _get_webhook_secret(platform: str, request: Request) -> str | None:
    """Get webhook secret for platform from configuration.

    In production, this would:
    1. Look up the connector config from database
    2. Get the webhook signing secret from platform-specific storage

    For Phase 10, use environment variables.

    Args:
        platform: Platform identifier.
        request: FastAPI request.

    Returns:
        Webhook secret string or None.
    """
    env_var_map = {
        "slack": "SAW_SLACK_SIGNING_SECRET",
        "github": "SAW_GITHUB_WEBHOOK_SECRET",
        "discord": "SAW_DISCORD_PUBLIC_KEY",
        "feishu": "SAW_FEISHU_SIGNING_SECRET",
    }
    return os.environ.get(env_var_map.get(platform, ""))


def _extract_text(platform: str, payload: dict) -> str:
    """Best-effort extraction of a text snippet from a webhook payload.

    F-CONN-06: platform-specific field paths; falls back to a truncated JSON
    dump so a verified webhook is never silently dropped.
    """
    try:
        if platform == "slack":
            event = payload.get("event", {}) or {}
            return (event.get("text") or payload.get("text") or "").strip()
        if platform == "github":
            action = payload.get("action", "")
            issue = payload.get("issue") or payload.get("pull_request") or {}
            title = issue.get("title", "")
            body = issue.get("body", "")
            return f"{action} {title}".strip() + (f"\n\n{body}" if body else "")
        if platform == "discord":
            return (
                payload.get("content")
                or (payload.get("data") or {}).get("content")
                or ""
            ).strip()
        if platform == "feishu":
            event = payload.get("event") or {}
            return (event.get("text") or event.get("content") or "").strip()
    except Exception:
        pass
    return json.dumps(payload, ensure_ascii=False)[:2000]