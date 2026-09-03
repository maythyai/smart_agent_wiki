"""FastAPI webhook endpoints for GitHub.

Plan 14-03: Webhooks and reconciliation.
Per GITH-05: Webhook endpoint for real-time updates.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from saw.db.session import get_db_session as get_session
from saw.connectors.github.webhook_handler import GitHubWebhookHandler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/github", tags=["webhooks"])


class WebhookResponse(BaseModel):
    """Response for webhook processing."""
    status: str
    message: Optional[str] = None
    items_count: int = 0


async def get_webhook_handler(
    session: AsyncSession = Depends(get_session)
) -> GitHubWebhookHandler:
    """Dependency to get webhook handler.

    Args:
        session: SQLAlchemy async session.

    Returns:
        GitHubWebhookHandler instance.
    """
    import os
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    # M-23: refuse to verify with an empty/default secret — anyone could forge
    # valid HMAC-SHA256 signatures against the empty-string secret. The unified
    # webhook endpoint already guards this (webhook_inbound.py); GitHub's own
    # endpoint must too.
    if not webhook_secret:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="GITHUB_WEBHOOK_SECRET not configured; GitHub webhook verification refused.",
        )
    return GitHubWebhookHandler(session=session, webhook_secret=webhook_secret)


@router.post("", response_model=WebhookResponse)
async def handle_github_webhook(
    request: Request,
    handler: GitHubWebhookHandler = Depends(get_webhook_handler),
) -> WebhookResponse:
    """Handle GitHub webhook POST request.

    Per GITH-05: Receive and process webhook events.
    Per GITH-06: Verify HMAC-SHA256 signature.

    Args:
        request: FastAPI request object.
        handler: Webhook handler dependency.

    Returns:
        WebhookResponse with processing status.
    """
    # Get raw body for signature verification
    payload_bytes = await request.body()

    # Get signature header
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature:
        raise HTTPException(401, "Missing webhook signature")

    # Verify signature
    if not await handler.verify_signature(payload_bytes, signature):
        raise HTTPException(401, "Invalid webhook signature")

    # Parse payload
    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON payload")

    # Parse event
    headers = dict(request.headers)
    event = handler.parse_event(headers, payload)

    # Check for duplicate delivery
    if await handler.is_duplicate_delivery(event.delivery_id):
        logger.info(f"Duplicate delivery: {event.delivery_id}")
        return WebhookResponse(status="duplicate_ignored")

    # Check if repository is selected
    if not await handler.is_repository_selected(event.repository):
        logger.info(f"Repository not selected: {event.repository}")
        return WebhookResponse(status="repository_not_selected")

    # Process event
    items = await handler.process_event(event)

    # Commit transaction
    await handler._session.commit()

    return WebhookResponse(
        status="processed",
        items_count=len(items),
    )


@router.get("/health")
async def webhook_health() -> dict:
    """Health check for webhook endpoint.

    Returns:
        Dict with status.
    """
    return {"status": "ok"}


@router.post("/reconcile")
async def trigger_reconciliation(
    repository: Optional[str] = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Trigger manual reconciliation.

    Args:
        repository: Optional specific repository to reconcile.
        session: SQLAlchemy async session.

    Returns:
        Dict with reconciliation results.
    """
    # F-CONN补审: reconciliation needs a configured connector instance.
    # Return an honest status instead of pretending it was triggered.
    return {
        "status": "not_implemented",
        "repository": repository,
        "message": "GitHub reconciliation requires a configured connector instance.",
    }
