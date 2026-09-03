"""GitHub webhook handler with signature verification.

Plan 14-03: Webhooks and reconciliation.
Per GITH-05: Real-time Issue/Discussion updates via webhooks.
Per GITH-06: Webhook signature verification.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saw.connectors.webhook_verifier import WebhookVerifier, SignatureVerificationError
from saw.connectors.github.models import GitHubWebhookEvent, GitHubIssue, GitHubComment
from saw.connectors.github.transformer import IssueTransformer, DiscussionTransformer
from saw.connectors.protocol import ConnectorItem
from saw.db.github_models import GitHubWebhookDeliveryModel, GitHubRepositoryConfigModel

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class GitHubWebhookHandler:
    """GitHub webhook event handler.

    Per GITH-05: Real-time updates via webhooks.
    Per GITH-06: HMAC-SHA256 signature verification.
    """

    def __init__(
        self,
        session: AsyncSession,
        webhook_secret: str,
    ) -> None:
        """Initialize webhook handler.

        Args:
            session: SQLAlchemy async session for database operations.
            webhook_secret: GitHub webhook secret for signature verification.
        """
        self._session = session
        self._webhook_secret = webhook_secret
        self._verifier = WebhookVerifier(secret=webhook_secret, platform="github")
        self._issue_transformer = IssueTransformer()
        self._discussion_transformer = DiscussionTransformer()

    async def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature.

        Per GITH-06: HMAC-SHA256 signature verification.

        Args:
            payload: Raw request body bytes.
            signature: X-Hub-Signature-256 header value.

        Returns:
            True if signature is valid.
        """
        try:
            return self._verifier._verify_github(payload, signature)
        except SignatureVerificationError:
            return False

    def parse_event(self, headers: dict, payload: dict) -> GitHubWebhookEvent:
        """Parse webhook event from headers and payload.

        Args:
            headers: Request headers dict.
            payload: JSON payload dict.

        Returns:
            GitHubWebhookEvent instance.
        """
        delivery_id = headers.get("X-GitHub-Delivery", "")
        event_type = headers.get("X-GitHub-Event", "")

        action = payload.get("action", "")
        repository = payload.get("repository", {}).get("full_name", "")
        sender = payload.get("sender", {}).get("login", "")

        return GitHubWebhookEvent(
            delivery_id=delivery_id,
            event_type=event_type,
            action=action,
            payload=payload,
            repository=repository,
            sender=sender,
            received_at=utcnow(),
        )

    async def is_duplicate_delivery(self, delivery_id: str) -> bool:
        """Check if delivery has already been processed.

        Per T-14-16: Deduplication within 24-hour window.

        Args:
            delivery_id: X-GitHub-Delivery UUID.

        Returns:
            True if duplicate (already processed).
        """
        stmt = select(GitHubWebhookDeliveryModel).where(
            GitHubWebhookDeliveryModel.delivery_id == delivery_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def is_repository_selected(self, repository: str) -> bool:
        """Check if repository is selected for sync.

        Args:
            repository: Repository full name (owner/repo).

        Returns:
            True if repository is selected.
        """
        stmt = (
            select(GitHubRepositoryConfigModel)
            .where(GitHubRepositoryConfigModel.repository_id == repository)
            .where(GitHubRepositoryConfigModel.is_selected == True)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def record_delivery(
        self,
        event: GitHubWebhookEvent,
        items_created: int = 0,
    ) -> None:
        """Record webhook delivery for deduplication.

        Args:
            event: GitHubWebhookEvent instance.
            items_created: Number of items created from this event.
        """
        delivery = GitHubWebhookDeliveryModel(
            delivery_id=event.delivery_id,
            event_type=event.event_type,
            repository=event.repository,
            action=event.action,
            items_created=items_created,
        )
        self._session.add(delivery)
        await self._session.flush()

    async def process_event(self, event: GitHubWebhookEvent) -> list[ConnectorItem]:
        """Process webhook event and return items.

        Dispatches to appropriate handler based on event type.

        Args:
            event: GitHubWebhookEvent instance.

        Returns:
            List of ConnectorItem created/updated.
        """
        handler_map = {
            "issues": self._handle_issue_event,
            "issue_comment": self._handle_comment_event,
            "discussion": self._handle_discussion_event,
            "discussion_comment": self._handle_discussion_comment_event,
        }

        handler = handler_map.get(event.event_type)
        if not handler:
            logger.info(f"Unhandled event type: {event.event_type}")
            return []

        try:
            items = await handler(event)
            await self.record_delivery(event, len(items))
            return items
        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
            await self.record_delivery(event, 0)
            return []

    async def _handle_issue_event(self, event: GitHubWebhookEvent) -> list[ConnectorItem]:
        """Handle issues event.

        Args:
            event: GitHubWebhookEvent with issues payload.

        Returns:
            List of ConnectorItem.
        """
        issue_data = event.payload.get("issue", {})
        repository = event.repository

        issue = self._parse_issue_from_webhook(issue_data, repository)
        self._issue_transformer.transform_to_claim(issue)

        item = ConnectorItem(
            id=f"github-issue-{repository}#{issue.number}",
            title=issue.title,
            content=issue.body or "",
            url=issue.html_url,
            author=issue.user.login,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            metadata={
                "platform": "github",
                "type": "issue",
                "repository": repository,
                "issue_number": issue.number,
                "state": issue.state,
                "action": event.action,
                "labels": [l.name for l in issue.labels],
            },
        )

        return [item]

    async def _handle_comment_event(self, event: GitHubWebhookEvent) -> list[ConnectorItem]:
        """Handle issue_comment event.

        Args:
            event: GitHubWebhookEvent with issue_comment payload.

        Returns:
            List of ConnectorItem.
        """
        comment_data = event.payload.get("comment", {})
        issue_data = event.payload.get("issue", {})
        repository = event.repository

        comment = self._parse_comment_from_webhook(comment_data, issue_data, repository)
        item = ConnectorItem(
            id=f"github-comment-{repository}#{comment.issue_number}-{comment.id}",
            title=f"Comment on #{comment.issue_number}",
            content=comment.body,
            url=comment.html_url,
            author=comment.user.login,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            metadata={
                "platform": "github",
                "type": "comment",
                "parent_type": "issue",
                "parent_number": comment.issue_number,
                "repository": repository,
            },
        )

        return [item]

    async def _handle_discussion_event(self, event: GitHubWebhookEvent) -> list[ConnectorItem]:
        """Handle discussion event.

        Args:
            event: GitHubWebhookEvent with discussion payload.

        Returns:
            List of ConnectorItem.
        """
        discussion_data = event.payload.get("discussion", {})
        repository = event.repository

        item = ConnectorItem(
            id=f"github-discussion-{repository}#{discussion_data.get('number', 0)}",
            title=discussion_data.get("title", ""),
            content=discussion_data.get("body", ""),
            url=discussion_data.get("html_url", ""),
            author=discussion_data.get("user", {}).get("login", ""),
            created_at=utcnow(),
            updated_at=utcnow(),
            metadata={
                "platform": "github",
                "type": "discussion",
                "repository": repository,
                "discussion_number": discussion_data.get("number", 0),
                "category": discussion_data.get("category", {}),
                "action": event.action,
            },
        )

        return [item]

    async def _handle_discussion_comment_event(self, event: GitHubWebhookEvent) -> list[ConnectorItem]:
        """Handle discussion_comment event.

        Args:
            event: GitHubWebhookEvent with discussion_comment payload.

        Returns:
            List of ConnectorItem.
        """
        comment_data = event.payload.get("comment", {})
        discussion_data = event.payload.get("discussion", {})
        repository = event.repository

        item = ConnectorItem(
            id=f"github-comment-{repository}#d{discussion_data.get('number', 0)}-{comment_data.get('id', 0)}",
            title=f"Comment on discussion #{discussion_data.get('number', 0)}",
            content=comment_data.get("body", ""),
            url=None,
            author=comment_data.get("user", {}).get("login", ""),
            created_at=utcnow(),
            updated_at=utcnow(),
            metadata={
                "platform": "github",
                "type": "comment",
                "parent_type": "discussion",
                "parent_number": discussion_data.get("number", 0),
                "repository": repository,
            },
        )

        return [item]

    def _parse_issue_from_webhook(self, data: dict, repository: str) -> GitHubIssue:
        """Parse issue from webhook payload.

        Args:
            data: Issue data dict.
            repository: Repository full name.

        Returns:
            GitHubIssue instance.
        """
        from saw.connectors.github.models import GitHubUser, GitHubLabel, GitHubMilestone

        user = GitHubUser(
            id=data.get("user", {}).get("id", 0),
            login=data.get("user", {}).get("login", ""),
            avatar_url=data.get("user", {}).get("avatar_url"),
            type="User",
        )

        labels = [
            GitHubLabel(
                id=l.get("id", 0),
                name=l.get("name", ""),
                color=l.get("color", "default"),
            )
            for l in data.get("labels", [])
        ]

        milestone_data = data.get("milestone")
        milestone = None
        if milestone_data:
            milestone = GitHubMilestone(
                id=milestone_data.get("id", 0),
                number=milestone_data.get("number", 0),
                title=milestone_data.get("title", ""),
                state=milestone_data.get("state", "open"),
            )

        assignees = [
            GitHubUser(
                id=a.get("id", 0),
                login=a.get("login", ""),
                type="User",
            )
            for a in data.get("assignees", [])
        ]

        return GitHubIssue(
            id=data.get("id", 0),
            number=data.get("number", 0),
            title=data.get("title", ""),
            body=data.get("body", ""),
            state=data.get("state", "open"),
            labels=labels,
            assignees=assignees,
            milestone=milestone,
            comments_count=data.get("comments", 0),
            created_at=self._parse_timestamp(data.get("created_at")),
            updated_at=self._parse_timestamp(data.get("updated_at")),
            closed_at=self._parse_timestamp(data.get("closed_at")),
            user=user,
            url=data.get("url", ""),
            html_url=data.get("html_url", ""),
            repository=repository,
        )

    def _parse_comment_from_webhook(
        self,
        comment_data: dict,
        issue_data: dict,
        repository: str,
    ) -> GitHubComment:
        """Parse comment from webhook payload.

        Args:
            comment_data: Comment data dict.
            issue_data: Parent issue data dict.
            repository: Repository full name.

        Returns:
            GitHubComment instance.
        """
        from saw.connectors.github.models import GitHubUser

        user = GitHubUser(
            id=comment_data.get("user", {}).get("id", 0),
            login=comment_data.get("user", {}).get("login", ""),
            avatar_url=comment_data.get("user", {}).get("avatar_url"),
            type="User",
        )

        return GitHubComment(
            id=comment_data.get("id", 0),
            body=comment_data.get("body", ""),
            user=user,
            created_at=self._parse_timestamp(comment_data.get("created_at")),
            updated_at=self._parse_timestamp(comment_data.get("updated_at")),
            issue_number=issue_data.get("number", 0),
            html_url=comment_data.get("html_url", ""),
        )

    def _parse_timestamp(self, ts: Optional[str]) -> datetime:
        """Parse ISO timestamp.

        Args:
            ts: ISO timestamp string.

        Returns:
            datetime object (UTC).
        """
        if not ts:
            return utcnow()

        # Handle both Z and +00:00 suffixes
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"

        return datetime.fromisoformat(ts)
