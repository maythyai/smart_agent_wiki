"""Tests for GitHub webhook handler.

Plan 14-03: Webhooks and reconciliation.
Per GITH-05: Webhook processing tests.
Per GITH-06: Signature verification tests.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from saw.connectors.github.webhook_handler import GitHubWebhookHandler
from saw.connectors.github.models import GitHubWebhookEvent
from saw.connectors.webhook_verifier import WebhookVerifier
from saw.connectors.protocol import ConnectorItem


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


@pytest.fixture
def mock_session() -> MagicMock:
    """Create mock database session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session


@pytest.fixture
def webhook_secret() -> str:
    """Webhook secret for testing."""
    return "test-webhook-secret"


class TestGitHubWebhookHandler:
    """Tests for GitHubWebhookHandler."""

    def test_parse_event(self, mock_session: MagicMock, webhook_secret: str) -> None:
        """Test parsing webhook event from headers and payload."""
        handler = GitHubWebhookHandler(
            session=mock_session,
            webhook_secret=webhook_secret,
        )

        headers = {
            "X-GitHub-Delivery": "12345678-1234-1234-1234-123456789012",
            "X-GitHub-Event": "issues",
        }
        payload = {
            "action": "opened",
            "repository": {"full_name": "owner/repo"},
            "sender": {"login": "testuser"},
        }

        event = handler.parse_event(headers, payload)

        assert event.delivery_id == "12345678-1234-1234-1234-123456789012"
        assert event.event_type == "issues"
        assert event.action == "opened"
        assert event.repository == "owner/repo"
        assert event.sender == "testuser"

    @pytest.mark.asyncio
    async def test_verify_signature_valid(
        self,
        mock_session: MagicMock,
        webhook_secret: str,
    ) -> None:
        """Test signature verification with valid signature."""
        handler = GitHubWebhookHandler(
            session=mock_session,
            webhook_secret=webhook_secret,
        )

        # Create valid signature
        payload = '{"test": "data"}'
        verifier = WebhookVerifier(secret=webhook_secret, platform="github")
        signature = verifier.compute_signature(webhook_secret, payload.encode(), "github")

        result = await handler.verify_signature(payload.encode(), signature)

        assert result is True

    @pytest.mark.asyncio
    async def test_verify_signature_invalid(
        self,
        mock_session: MagicMock,
        webhook_secret: str,
    ) -> None:
        """Test signature verification with invalid signature."""
        handler = GitHubWebhookHandler(
            session=mock_session,
            webhook_secret=webhook_secret,
        )

        payload = '{"test": "data"}'
        invalid_signature = "sha256=invalid"

        result = await handler.verify_signature(payload.encode(), invalid_signature)

        assert result is False

    @pytest.mark.asyncio
    async def test_is_duplicate_delivery(
        self,
        mock_session: MagicMock,
        webhook_secret: str,
    ) -> None:
        """Test duplicate delivery detection."""
        handler = GitHubWebhookHandler(
            session=mock_session,
            webhook_secret=webhook_secret,
        )

        # Mock existing delivery
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_session.execute.return_value = mock_result

        is_duplicate = await handler.is_duplicate_delivery("existing-delivery-id")

        assert is_duplicate is True

    @pytest.mark.asyncio
    async def test_is_duplicate_delivery_not_found(
        self,
        mock_session: MagicMock,
        webhook_secret: str,
    ) -> None:
        """Test duplicate detection for new delivery."""
        handler = GitHubWebhookHandler(
            session=mock_session,
            webhook_secret=webhook_secret,
        )

        # Mock no existing delivery
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        is_duplicate = await handler.is_duplicate_delivery("new-delivery-id")

        assert is_duplicate is False

    @pytest.mark.asyncio
    async def test_is_repository_selected(
        self,
        mock_session: MagicMock,
        webhook_secret: str,
    ) -> None:
        """Test repository selection check."""
        handler = GitHubWebhookHandler(
            session=mock_session,
            webhook_secret=webhook_secret,
        )

        # Mock selected repository
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_session.execute.return_value = mock_result

        is_selected = await handler.is_repository_selected("owner/repo")

        assert is_selected is True

    @pytest.mark.asyncio
    async def test_is_repository_not_selected(
        self,
        mock_session: MagicMock,
        webhook_secret: str,
    ) -> None:
        """Test repository not selected."""
        handler = GitHubWebhookHandler(
            session=mock_session,
            webhook_secret=webhook_secret,
        )

        # Mock not selected
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        is_selected = await handler.is_repository_selected("owner/not-selected")

        assert is_selected is False

    @pytest.mark.asyncio
    async def test_process_issue_event(
        self,
        mock_session: MagicMock,
        webhook_secret: str,
    ) -> None:
        """Test processing issues event."""
        handler = GitHubWebhookHandler(
            session=mock_session,
            webhook_secret=webhook_secret,
        )

        event = GitHubWebhookEvent(
            delivery_id="test-delivery",
            event_type="issues",
            action="opened",
            payload={
                "issue": {
                    "id": 123,
                    "number": 42,
                    "title": "Test Issue",
                    "body": "Issue body",
                    "state": "open",
                    "labels": [],
                    "user": {"id": 1, "login": "testuser"},
                    "created_at": utcnow().isoformat(),
                    "updated_at": utcnow().isoformat(),
                    "html_url": "https://github.com/owner/repo/issues/42",
                },
            },
            repository="owner/repo",
            sender="testuser",
        )

        items = await handler.process_event(event)

        assert len(items) == 1
        assert items[0].title == "Test Issue"
        assert items[0].metadata["type"] == "issue"

    @pytest.mark.asyncio
    async def test_process_comment_event(
        self,
        mock_session: MagicMock,
        webhook_secret: str,
    ) -> None:
        """Test processing issue_comment event."""
        handler = GitHubWebhookHandler(
            session=mock_session,
            webhook_secret=webhook_secret,
        )

        event = GitHubWebhookEvent(
            delivery_id="test-delivery",
            event_type="issue_comment",
            action="created",
            payload={
                "comment": {
                    "id": 999,
                    "body": "Comment body",
                    "user": {"id": 1, "login": "commenter"},
                    "created_at": utcnow().isoformat(),
                    "updated_at": utcnow().isoformat(),
                    "html_url": "https://github.com/owner/repo/issues/42#issuecomment-999",
                },
                "issue": {
                    "number": 42,
                },
            },
            repository="owner/repo",
            sender="commenter",
        )

        items = await handler.process_event(event)

        assert len(items) == 1
        assert items[0].metadata["type"] == "comment"
        assert items[0].metadata["parent_type"] == "issue"

    @pytest.mark.asyncio
    async def test_process_discussion_event(
        self,
        mock_session: MagicMock,
        webhook_secret: str,
    ) -> None:
        """Test processing discussion event."""
        handler = GitHubWebhookHandler(
            session=mock_session,
            webhook_secret=webhook_secret,
        )

        event = GitHubWebhookEvent(
            delivery_id="test-delivery",
            event_type="discussion",
            action="created",
            payload={
                "discussion": {
                    "id": "disc1",
                    "number": 1,
                    "title": "Test Discussion",
                    "body": "Discussion body",
                    "user": {"login": "discusser"},
                    "category": {"name": "Q&A", "slug": "q-a"},
                    "html_url": "https://github.com/owner/repo/discussions/1",
                },
            },
            repository="owner/repo",
            sender="discusser",
        )

        items = await handler.process_event(event)

        assert len(items) == 1
        assert items[0].metadata["type"] == "discussion"

    @pytest.mark.asyncio
    async def test_process_unknown_event(
        self,
        mock_session: MagicMock,
        webhook_secret: str,
    ) -> None:
        """Test processing unknown event type."""
        handler = GitHubWebhookHandler(
            session=mock_session,
            webhook_secret=webhook_secret,
        )

        event = GitHubWebhookEvent(
            delivery_id="test-delivery",
            event_type="unknown",
            action="action",
            payload={},
            repository="owner/repo",
            sender="testuser",
        )

        items = await handler.process_event(event)

        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_record_delivery(
        self,
        mock_session: MagicMock,
        webhook_secret: str,
    ) -> None:
        """Test recording webhook delivery."""
        handler = GitHubWebhookHandler(
            session=mock_session,
            webhook_secret=webhook_secret,
        )

        event = GitHubWebhookEvent(
            delivery_id="test-delivery",
            event_type="issues",
            action="opened",
            payload={},
            repository="owner/repo",
            sender="testuser",
        )

        await handler.record_delivery(event, items_created=1)

        # Should add delivery record
        assert mock_session.add.called