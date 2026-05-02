"""GitHub transformer for Issues, Discussions, and Comments.

Plan 14-02: Issue/Discussion ingestion with GraphQL.
Per GITH-03: Issue to Claim transformation.
Per GITH-04: Discussion to Claim transformation.
Per GITH-07: Label to tag mapping.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
import logging

from saw.connectors.github.models import (
    GitHubIssue,
    GitHubComment,
    GitHubDiscussion,
)
from saw.connectors.protocol import ConnectorItem

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class IssueTransformer:
    """Transformer for GitHub Issues to SAW Claims.

    Per GITH-03: Issue to Claim transformation.
    Per GITH-07: Label to tag mapping.
    """

    def __init__(self, label_tag_mapping: Optional[dict[str, str]] = None) -> None:
        """Initialize issue transformer.

        Args:
            label_tag_mapping: Custom mapping from GitHub labels to SAW tags.
        """
        self._label_tag_mapping = label_tag_mapping or {}
        self._default_mapping = {
            "bug": "bug",
            "enhancement": "feature",
            "documentation": "docs",
            "question": "help",
            "wontfix": "wontfix",
            "duplicate": "duplicate",
            "good first issue": "good-first-issue",
            "help wanted": "help-wanted",
        }

    def transform_to_claim(self, issue: GitHubIssue) -> dict:
        """Transform GitHub issue to SAW Claim dict.

        Args:
            issue: GitHubIssue model instance.

        Returns:
            Dict matching Claim schema.
        """
        return {
            "external_id": f"github-issue-{issue.repository}#{issue.number}",
            "title": issue.title,
            "content": issue.body or "",
            "source_url": issue.html_url,
            "author": issue.user.login,
            "created_at": issue.created_at.isoformat() if issue.created_at else None,
            "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
            "confidence": self._derive_confidence(issue),
            "freshness": self._derive_freshness(issue),
            "tags": self._map_labels_to_tags(issue.labels),
            "metadata": {
                "platform": "github",
                "type": "issue",
                "repository": issue.repository,
                "issue_number": issue.number,
                "state": issue.state,
                "labels": [label.name for label in issue.labels],
                "assignees": [a.login for a in issue.assignees],
                "milestone": issue.milestone.title if issue.milestone else None,
                "comments_count": issue.comments_count,
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
            },
            "related_claims": [],  # Populated when comments fetched
        }

    def _map_labels_to_tags(self, labels: list[Any]) -> list[str]:
        """Map GitHub labels to SAW tags.

        Per GITH-07: Label to tag mapping.

        Args:
            labels: List of GitHubLabel objects.

        Returns:
            List of SAW tag strings.
        """
        tags: list[str] = []

        for label in labels:
            label_name = label.name.lower()

            # Check custom mapping first
            if label_name in self._label_tag_mapping:
                tag = self._label_tag_mapping[label_name]
                if tag and tag not in tags:
                    tags.append(tag)
            # Check default mapping
            elif label_name in self._default_mapping:
                tag = self._default_mapping[label_name]
                if tag not in tags:
                    tags.append(tag)
            else:
                # Default: sanitize label name
                tag = label_name.replace(" ", "-").replace("/", "-")
                if tag and tag not in tags:
                    tags.append(tag)

        return tags

    def _derive_confidence(self, issue: GitHubIssue) -> str:
        """Derive confidence level from issue state.

        Args:
            issue: GitHubIssue model instance.

        Returns:
            Confidence level string.
        """
        # Higher confidence for closed issues with milestone
        if issue.state == "closed" and issue.milestone:
            return "cross_validated"

        # Higher confidence for issues with multiple assignees
        if len(issue.assignees) >= 2:
            return "cross_validated"

        # Single assignee or closed
        if issue.assignees or issue.state == "closed":
            return "single_source"

        return "unverified"

    def _derive_freshness(self, issue: GitHubIssue) -> str:
        """Derive freshness level from issue update time.

        Args:
            issue: GitHubIssue model instance.

        Returns:
            Freshness level string.
        """
        now = utcnow()

        # Closed issues are historical
        if issue.state == "closed":
            return "historical"

        if not issue.updated_at:
            return "rotten"

        delta = now - issue.updated_at

        if delta.days < 30:
            return "fresh"
        elif delta.days < 180:
            return "stale"
        else:
            return "rotten"

    def transform_comment_to_claim(
        self,
        comment: GitHubComment,
        parent_issue: GitHubIssue,
    ) -> dict:
        """Transform GitHub comment to related Claim dict.

        Args:
            comment: GitHubComment model instance.
            parent_issue: Parent GitHubIssue model instance.

        Returns:
            Dict matching Claim schema.
        """
        return {
            "external_id": f"github-comment-{parent_issue.repository}#{parent_issue.number}-{comment.id}",
            "title": f"Comment on #{parent_issue.number}: {parent_issue.title[:50]}",
            "content": comment.body,
            "source_url": comment.html_url,
            "author": comment.user.login,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
            "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
            "confidence": "unverified",
            "freshness": "fresh",
            "tags": [],
            "metadata": {
                "platform": "github",
                "type": "comment",
                "parent_type": "issue",
                "parent_number": parent_issue.number,
                "parent_id": parent_issue.id,
                "repository": parent_issue.repository,
            },
        }


class DiscussionTransformer:
    """Transformer for GitHub Discussions to SAW Claims.

    Per GITH-04: Discussion to Claim transformation.
    """

    def __init__(self) -> None:
        """Initialize discussion transformer."""
        pass

    def transform_to_claim(self, discussion: GitHubDiscussion) -> dict:
        """Transform GitHub discussion to SAW Claim dict.

        Args:
            discussion: GitHubDiscussion model instance.

        Returns:
            Dict matching Claim schema.
        """
        return {
            "external_id": f"github-discussion-{discussion.repository}#{discussion.number}",
            "title": discussion.title,
            "content": discussion.body or "",
            "source_url": discussion.url,
            "author": discussion.author.login,
            "created_at": discussion.created_at.isoformat() if discussion.created_at else None,
            "updated_at": discussion.updated_at.isoformat() if discussion.updated_at else None,
            "confidence": self._derive_confidence(discussion),
            "freshness": self._derive_freshness(discussion),
            "tags": [discussion.category.name],  # Category as tag
            "metadata": {
                "platform": "github",
                "type": "discussion",
                "repository": discussion.repository,
                "discussion_number": discussion.number,
                "category": {
                    "id": discussion.category.id,
                    "name": discussion.category.name,
                    "slug": discussion.category.slug,
                },
                "answer_id": discussion.answer_id,
                "upvote_count": discussion.upvote_count,
                "comments_count": discussion.comments_count,
            },
        }

    def _derive_confidence(self, discussion: GitHubDiscussion) -> str:
        """Derive confidence level from discussion state.

        Args:
            discussion: GitHubDiscussion model instance.

        Returns:
            Confidence level string.
        """
        # Has answer = cross_validated
        if discussion.answer_id:
            return "cross_validated"

        # High upvotes = single_source
        if discussion.upvote_count >= 10:
            return "single_source"

        return "unverified"

    def _derive_freshness(self, discussion: GitHubDiscussion) -> str:
        """Derive freshness level from discussion update time.

        Args:
            discussion: GitHubDiscussion model instance.

        Returns:
            Freshness level string.
        """
        now = utcnow()

        if not discussion.updated_at:
            return "rotten"

        delta = now - discussion.updated_at

        if delta.days < 30:
            return "fresh"
        elif delta.days < 180:
            return "stale"
        else:
            return "rotten"

    def transform_comment_to_claim(
        self,
        comment: GitHubComment,
        parent_discussion: GitHubDiscussion,
    ) -> dict:
        """Transform GitHub discussion comment to related Claim dict.

        Args:
            comment: GitHubComment model instance.
            parent_discussion: Parent GitHubDiscussion model instance.

        Returns:
            Dict matching Claim schema.
        """
        return {
            "external_id": f"github-comment-{parent_discussion.repository}#d{parent_discussion.number}-{comment.id}",
            "title": f"Comment on #{parent_discussion.number}: {parent_discussion.title[:50]}",
            "content": comment.body,
            "source_url": None,  # Discussion comments don't have individual URLs
            "author": comment.user.login,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
            "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
            "confidence": "unverified",
            "freshness": "fresh",
            "tags": [],
            "metadata": {
                "platform": "github",
                "type": "comment",
                "parent_type": "discussion",
                "parent_number": parent_discussion.number,
                "parent_id": parent_discussion.id,
                "repository": parent_discussion.repository,
            },
        }


class GitHubTransformer:
    """Facade for GitHub transformations.

    Combines IssueTransformer and DiscussionTransformer.
    """

    def __init__(
        self,
        label_tag_mapping: Optional[dict[str, str]] = None,
    ) -> None:
        """Initialize GitHub transformer.

        Args:
            label_tag_mapping: Custom mapping from GitHub labels to SAW tags.
        """
        self._issue_transformer = IssueTransformer(label_tag_mapping)
        self._discussion_transformer = DiscussionTransformer()

    def transform_to_claim(self, item: ConnectorItem) -> dict:
        """Transform ConnectorItem to SAW Claim dict.

        Dispatches based on item.metadata["type"].

        Args:
            item: ConnectorItem from GitHub connector.

        Returns:
            Dict matching Claim schema.
        """
        item_type = item.metadata.get("type")

        if item_type == "issue":
            # Create a minimal GitHubIssue from item
            issue = self._item_to_issue(item)
            return self._issue_transformer.transform_to_claim(issue)
        elif item_type == "discussion":
            # Create a minimal GitHubDiscussion from item
            discussion = self._item_to_discussion(item)
            return self._discussion_transformer.transform_to_claim(discussion)
        elif item_type == "comment":
            # Comments handled separately
            return self._transform_comment_item(item)
        else:
            # Default transformation
            return self._default_transform(item)

    def transform_from_claim(self, claim: dict, target_type: str = "comment") -> ConnectorItem:
        """Transform SAW Claim dict to GitHub ConnectorItem.

        Used for push operations (posting comments).

        Args:
            claim: SAW Claim dict.
            target_type: Target item type (issue, discussion, comment).

        Returns:
            ConnectorItem ready for GitHub push.
        """
        return ConnectorItem(
            id=claim.get("external_id", ""),
            title=claim.get("title", ""),
            content=claim.get("content", ""),
            url=claim.get("source_url"),
            author=claim.get("author"),
            created_at=None,
            updated_at=None,
            metadata={
                "parent_type": claim.get("metadata", {}).get("parent_type", target_type),
                "parent_number": claim.get("metadata", {}).get("parent_number"),
                "repository": claim.get("metadata", {}).get("repository"),
            },
        )

    def _item_to_issue(self, item: ConnectorItem) -> GitHubIssue:
        """Convert ConnectorItem to GitHubIssue.

        Args:
            item: ConnectorItem with issue data.

        Returns:
            GitHubIssue model instance.
        """
        from saw.connectors.github.models import GitHubUser, GitHubLabel

        return GitHubIssue(
            id=int(item.metadata.get("issue_id", 0)),
            number=item.metadata.get("issue_number", 0),
            title=item.title,
            body=item.content,
            state=item.metadata.get("state", "open"),
            labels=[
                GitHubLabel(id=0, name=label)
                for label in item.metadata.get("labels", [])
            ],
            assignees=[],
            milestone=None,
            comments_count=item.metadata.get("comments_count", 0),
            created_at=item.created_at or utcnow(),
            updated_at=item.updated_at or utcnow(),
            closed_at=None,
            user=GitHubUser(id=0, login=item.author or ""),
            url=item.url or "",
            html_url=item.url or "",
            repository=item.metadata.get("repository", ""),
        )

    def _item_to_discussion(self, item: ConnectorItem) -> GitHubDiscussion:
        """Convert ConnectorItem to GitHubDiscussion.

        Args:
            item: ConnectorItem with discussion data.

        Returns:
            GitHubDiscussion model instance.
        """
        from saw.connectors.github.models import GitHubUser, GitHubDiscussionCategory

        return GitHubDiscussion(
            id=item.id,
            number=item.metadata.get("discussion_number", 0),
            title=item.title,
            body=item.content,
            category=GitHubDiscussionCategory(
                id="",
                name=item.metadata.get("category", {}).get("name", ""),
                slug=item.metadata.get("category", {}).get("slug", ""),
            ),
            answer_id=item.metadata.get("answer_id"),
            upvote_count=item.metadata.get("upvote_count", 0),
            comments_count=item.metadata.get("comments_count", 0),
            author=GitHubUser(id=0, login=item.author or ""),
            created_at=item.created_at or utcnow(),
            updated_at=item.updated_at or utcnow(),
            url=item.url or "",
            repository=item.metadata.get("repository", ""),
        )

    def _transform_comment_item(self, item: ConnectorItem) -> dict:
        """Transform comment ConnectorItem to Claim dict.

        Args:
            item: ConnectorItem with comment data.

        Returns:
            Dict matching Claim schema.
        """
        return {
            "external_id": item.id,
            "title": f"Comment on {item.metadata.get('parent_type', 'item')}",
            "content": item.content,
            "source_url": item.url,
            "author": item.author,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "confidence": "unverified",
            "freshness": "fresh",
            "tags": [],
            "metadata": item.metadata,
        }

    def _default_transform(self, item: ConnectorItem) -> dict:
        """Default transformation for unknown item types.

        Args:
            item: ConnectorItem instance.

        Returns:
            Dict matching Claim schema.
        """
        return {
            "external_id": item.id,
            "title": item.title,
            "content": item.content,
            "source_url": item.url,
            "author": item.author,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            "confidence": "unverified",
            "freshness": "fresh",
            "tags": [],
            "metadata": item.metadata,
        }
