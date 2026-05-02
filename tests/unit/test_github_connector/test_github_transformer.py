"""Tests for GitHub transformer.

Plan 14-02: Issue/Discussion ingestion with GraphQL.
Per GITH-03: Issue to Claim transformation.
Per GITH-07: Label to tag mapping.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest

from saw.connectors.github.transformer import (
    IssueTransformer,
    DiscussionTransformer,
    GitHubTransformer,
)
from saw.connectors.github.models import (
    GitHubUser,
    GitHubLabel,
    GitHubMilestone,
    GitHubIssue,
    GitHubComment,
    GitHubDiscussion,
    GitHubDiscussionCategory,
)
from saw.connectors.protocol import ConnectorItem


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class TestIssueTransformer:
    """Tests for IssueTransformer."""

    def test_transform_to_claim(self) -> None:
        """Test basic issue transformation."""
        user = GitHubUser(id=1, login="testuser")
        issue = GitHubIssue(
            id=123,
            number=42,
            title="Test Issue",
            body="Issue body content",
            state="open",
            labels=[],
            assignees=[],
            milestone=None,
            comments_count=5,
            created_at=utcnow(),
            updated_at=utcnow(),
            closed_at=None,
            user=user,
            url="https://api.github.com/repos/owner/repo/issues/42",
            html_url="https://github.com/owner/repo/issues/42",
            repository="owner/repo",
        )

        transformer = IssueTransformer()
        claim = transformer.transform_to_claim(issue)

        assert claim["title"] == "Test Issue"
        assert claim["content"] == "Issue body content"
        assert claim["external_id"] == "github-issue-owner/repo#42"
        assert claim["source_url"] == "https://github.com/owner/repo/issues/42"
        assert claim["author"] == "testuser"
        assert claim["metadata"]["platform"] == "github"
        assert claim["metadata"]["type"] == "issue"
        assert claim["metadata"]["repository"] == "owner/repo"

    def test_label_to_tag_mapping_default(self) -> None:
        """Test default label to tag mapping."""
        user = GitHubUser(id=1, login="testuser")
        labels = [
            GitHubLabel(id=1, name="bug", color="red"),
            GitHubLabel(id=2, name="enhancement", color="blue"),
        ]
        issue = GitHubIssue(
            id=123,
            number=1,
            title="Issue",
            body="",
            state="open",
            labels=labels,
            assignees=[],
            milestone=None,
            comments_count=0,
            created_at=utcnow(),
            updated_at=utcnow(),
            user=user,
            url="",
            html_url="",
            repository="owner/repo",
        )

        transformer = IssueTransformer()
        claim = transformer.transform_to_claim(issue)

        assert "bug" in claim["tags"]
        assert "feature" in claim["tags"]  # enhancement -> feature

    def test_label_to_tag_mapping_custom(self) -> None:
        """Test custom label to tag mapping."""
        user = GitHubUser(id=1, login="testuser")
        labels = [
            GitHubLabel(id=1, name="bug", color="red"),
            GitHubLabel(id=2, name="custom-label", color="blue"),
        ]
        issue = GitHubIssue(
            id=123,
            number=1,
            title="Issue",
            body="",
            state="open",
            labels=labels,
            assignees=[],
            milestone=None,
            comments_count=0,
            created_at=utcnow(),
            updated_at=utcnow(),
            user=user,
            url="",
            html_url="",
            repository="owner/repo",
        )

        custom_mapping = {"bug": "critical", "custom-label": "my-tag"}
        transformer = IssueTransformer(label_tag_mapping=custom_mapping)
        claim = transformer.transform_to_claim(issue)

        assert "critical" in claim["tags"]  # bug -> critical via custom mapping
        assert "my-tag" in claim["tags"]

    def test_confidence_derivation(self) -> None:
        """Test confidence derivation from issue state."""
        user = GitHubUser(id=1, login="testuser")

        # Closed with milestone = cross_validated
        milestone = GitHubMilestone(id=1, number=1, title="v1.0")
        closed_issue = GitHubIssue(
            id=1,
            number=1,
            title="Closed",
            body="",
            state="closed",
            labels=[],
            assignees=[],
            milestone=milestone,
            comments_count=0,
            created_at=utcnow(),
            updated_at=utcnow(),
            closed_at=utcnow(),
            user=user,
            url="",
            html_url="",
            repository="owner/repo",
        )

        transformer = IssueTransformer()
        claim = transformer.transform_to_claim(closed_issue)

        assert claim["confidence"] == "cross_validated"

        # Open with no assignee = unverified
        open_issue = GitHubIssue(
            id=2,
            number=2,
            title="Open",
            body="",
            state="open",
            labels=[],
            assignees=[],
            milestone=None,
            comments_count=0,
            created_at=utcnow(),
            updated_at=utcnow(),
            user=user,
            url="",
            html_url="",
            repository="owner/repo",
        )
        claim = transformer.transform_to_claim(open_issue)
        assert claim["confidence"] == "unverified"

    def test_freshness_derivation(self) -> None:
        """Test freshness derivation from update time."""
        user = GitHubUser(id=1, login="testuser")

        # Fresh: updated within 30 days
        fresh_issue = GitHubIssue(
            id=1,
            number=1,
            title="Fresh",
            body="",
            state="open",
            labels=[],
            assignees=[],
            milestone=None,
            comments_count=0,
            created_at=utcnow(),
            updated_at=utcnow() - timedelta(days=10),
            user=user,
            url="",
            html_url="",
            repository="owner/repo",
        )

        transformer = IssueTransformer()
        claim = transformer.transform_to_claim(fresh_issue)

        assert claim["freshness"] == "fresh"

        # Stale: updated within 180 days
        stale_issue = GitHubIssue(
            id=2,
            number=2,
            title="Stale",
            body="",
            state="open",
            labels=[],
            assignees=[],
            milestone=None,
            comments_count=0,
            created_at=utcnow(),
            updated_at=utcnow() - timedelta(days=60),
            user=user,
            url="",
            html_url="",
            repository="owner/repo",
        )
        claim = transformer.transform_to_claim(stale_issue)
        assert claim["freshness"] == "stale"

        # Closed = historical
        closed_issue = GitHubIssue(
            id=3,
            number=3,
            title="Closed",
            body="",
            state="closed",
            labels=[],
            assignees=[],
            milestone=None,
            comments_count=0,
            created_at=utcnow(),
            updated_at=utcnow() - timedelta(days=10),
            closed_at=utcnow(),
            user=user,
            url="",
            html_url="",
            repository="owner/repo",
        )
        claim = transformer.transform_to_claim(closed_issue)
        assert claim["freshness"] == "historical"

    def test_transform_comment_to_claim(self) -> None:
        """Test comment transformation."""
        user = GitHubUser(id=1, login="commenter")
        issue_user = GitHubUser(id=2, login="issueauthor")
        issue = GitHubIssue(
            id=123,
            number=42,
            title="Test Issue",
            body="Issue body",
            state="open",
            labels=[],
            assignees=[],
            milestone=None,
            comments_count=1,
            created_at=utcnow(),
            updated_at=utcnow(),
            user=issue_user,
            url="",
            html_url="https://github.com/owner/repo/issues/42",
            repository="owner/repo",
        )
        comment = GitHubComment(
            id=999,
            body="Comment body",
            user=user,
            created_at=utcnow(),
            updated_at=utcnow(),
            issue_number=42,
            html_url="https://github.com/owner/repo/issues/42#issuecomment-999",
        )

        transformer = IssueTransformer()
        claim = transformer.transform_comment_to_claim(comment, issue)

        assert "Comment on #42" in claim["title"]
        assert claim["content"] == "Comment body"
        assert claim["metadata"]["parent_type"] == "issue"
        assert claim["metadata"]["parent_number"] == 42


class TestDiscussionTransformer:
    """Tests for DiscussionTransformer."""

    def test_transform_to_claim(self) -> None:
        """Test basic discussion transformation."""
        author = GitHubUser(id=1, login="discusser")
        category = GitHubDiscussionCategory(id="cat1", name="Q&A", slug="q-a")
        discussion = GitHubDiscussion(
            id="disc1",
            number=1,
            title="How to do X?",
            body="Discussion content",
            category=category,
            answer_id=None,
            upvote_count=5,
            comments_count=3,
            author=author,
            created_at=utcnow(),
            updated_at=utcnow(),
            url="https://github.com/owner/repo/discussions/1",
            repository="owner/repo",
        )

        transformer = DiscussionTransformer()
        claim = transformer.transform_to_claim(discussion)

        assert claim["title"] == "How to do X?"
        assert claim["content"] == "Discussion content"
        assert claim["external_id"] == "github-discussion-owner/repo#1"
        assert "Q&A" in claim["tags"]  # Category as tag
        assert claim["metadata"]["type"] == "discussion"

    def test_confidence_with_answer(self) -> None:
        """Test confidence derivation when answered."""
        author = GitHubUser(id=1, login="discusser")
        category = GitHubDiscussionCategory(id="cat1", name="Q&A", slug="q-a")
        discussion = GitHubDiscussion(
            id="disc1",
            number=1,
            title="Answered question",
            body="",
            category=category,
            answer_id="answer123",
            upvote_count=2,
            comments_count=5,
            author=author,
            created_at=utcnow(),
            updated_at=utcnow(),
            url="",
            repository="owner/repo",
        )

        transformer = DiscussionTransformer()
        claim = transformer.transform_to_claim(discussion)

        assert claim["confidence"] == "cross_validated"

    def test_confidence_with_upvotes(self) -> None:
        """Test confidence derivation with high upvotes."""
        author = GitHubUser(id=1, login="discusser")
        category = GitHubDiscussionCategory(id="cat1", name="Q&A", slug="q-a")
        discussion = GitHubDiscussion(
            id="disc1",
            number=1,
            title="Popular discussion",
            body="",
            category=category,
            answer_id=None,
            upvote_count=15,
            comments_count=10,
            author=author,
            created_at=utcnow(),
            updated_at=utcnow(),
            url="",
            repository="owner/repo",
        )

        transformer = DiscussionTransformer()
        claim = transformer.transform_to_claim(discussion)

        assert claim["confidence"] == "single_source"

    def test_transform_comment_to_claim(self) -> None:
        """Test discussion comment transformation."""
        author = GitHubUser(id=1, login="discusser")
        commenter = GitHubUser(id=2, login="commenter")
        category = GitHubDiscussionCategory(id="cat1", name="Q&A", slug="q-a")
        discussion = GitHubDiscussion(
            id="disc1",
            number=1,
            title="Discussion",
            body="",
            category=category,
            answer_id=None,
            upvote_count=0,
            comments_count=1,
            author=author,
            created_at=utcnow(),
            updated_at=utcnow(),
            url="",
            repository="owner/repo",
        )
        comment = GitHubComment(
            id=999,
            body="Discussion comment",
            user=commenter,
            created_at=utcnow(),
            updated_at=utcnow(),
            discussion_number=1,
        )

        transformer = DiscussionTransformer()
        claim = transformer.transform_comment_to_claim(comment, discussion)

        assert "Comment on #1" in claim["title"]
        assert claim["metadata"]["parent_type"] == "discussion"


class TestGitHubTransformer:
    """Tests for GitHubTransformer facade."""

    def test_transform_issue_item(self) -> None:
        """Test transforming issue ConnectorItem."""
        item = ConnectorItem(
            id="github-issue-owner/repo#42",
            title="Test Issue",
            content="Issue body",
            url="https://github.com/owner/repo/issues/42",
            author="testuser",
            created_at=utcnow(),
            updated_at=utcnow(),
            metadata={
                "platform": "github",
                "type": "issue",
                "repository": "owner/repo",
                "issue_number": 42,
                "state": "open",
                "labels": ["bug"],
                "comments_count": 0,
            },
        )

        transformer = GitHubTransformer()
        claim = transformer.transform_to_claim(item)

        assert claim["title"] == "Test Issue"
        assert claim["metadata"]["type"] == "issue"

    def test_transform_discussion_item(self) -> None:
        """Test transforming discussion ConnectorItem."""
        item = ConnectorItem(
            id="github-discussion-owner/repo#1",
            title="Discussion Title",
            content="Discussion body",
            url="https://github.com/owner/repo/discussions/1",
            author="discusser",
            created_at=utcnow(),
            updated_at=utcnow(),
            metadata={
                "platform": "github",
                "type": "discussion",
                "repository": "owner/repo",
                "discussion_number": 1,
                "category": {"name": "Q&A", "slug": "q-a"},
                "upvote_count": 5,
                "comments_count": 3,
            },
        )

        transformer = GitHubTransformer()
        claim = transformer.transform_to_claim(item)

        assert claim["title"] == "Discussion Title"
        assert claim["metadata"]["type"] == "discussion"

    def test_transform_from_claim(self) -> None:
        """Test transforming claim to ConnectorItem for push."""
        claim = {
            "content": "Comment content",
            "author": "commenter",
            "metadata": {
                "parent_type": "issue",
                "parent_number": 42,
                "repository": "owner/repo",
            },
        }

        transformer = GitHubTransformer()
        item = transformer.transform_from_claim(claim, target_type="comment")

        assert item.content == "Comment content"
        assert item.metadata["parent_type"] == "issue"
        assert item.metadata["parent_number"] == 42
        assert item.metadata["repository"] == "owner/repo"

    def test_custom_label_mapping(self) -> None:
        """Test custom label mapping in facade."""
        custom_mapping = {"bug": "critical-issue"}
        transformer = GitHubTransformer(label_tag_mapping=custom_mapping)

        assert transformer._issue_transformer._label_tag_mapping == custom_mapping