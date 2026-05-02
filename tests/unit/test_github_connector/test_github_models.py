"""Tests for GitHub connector models.

Plan 14-01: GitHub connector core with OAuth/App auth.
Per GITH-01: Test GitHub API models for Issues, Discussions, Repositories.
"""
from __future__ import annotations

from datetime import datetime, timezone
import pytest

from saw.connectors.github.models import (
    GitHubUser,
    GitHubLabel,
    GitHubMilestone,
    GitHubIssue,
    GitHubComment,
    GitHubDiscussion,
    GitHubDiscussionCategory,
    GitHubRepository,
    GitHubRateLimit,
    GitHubSearchResult,
    GitHubWebhookEvent,
    GitHubAuthType,
    GitHubAppInstallation,
)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class TestGitHubUser:
    """Tests for GitHubUser model."""

    def test_github_user_basic(self) -> None:
        """Test basic GitHubUser instantiation."""
        user = GitHubUser(
            id=12345,
            login="testuser",
            avatar_url="https://avatars.githubusercontent.com/u/12345",
            type="User",
            html_url="https://github.com/testuser",
        )
        assert user.id == 12345
        assert user.login == "testuser"
        assert user.type == "User"

    def test_github_user_bot(self) -> None:
        """Test GitHubUser for bot type."""
        user = GitHubUser(
            id=123456,
            login="dependabot[bot]",
            type="Bot",
        )
        assert user.type == "Bot"

    def test_github_user_from_attributes(self) -> None:
        """Test GitHubUser with from_attributes (ORM mode)."""
        class MockUser:
            id = 789
            login = "mockuser"
            avatar_url = None
            type = "User"
            html_url = None

        user = GitHubUser.model_validate(MockUser())
        assert user.id == 789
        assert user.login == "mockuser"


class TestGitHubLabel:
    """Tests for GitHubLabel model."""

    def test_github_label_basic(self) -> None:
        """Test basic GitHubLabel instantiation."""
        label = GitHubLabel(
            id=1,
            name="bug",
            color="d73a4a",
            description="Something isn't working",
        )
        assert label.id == 1
        assert label.name == "bug"
        assert label.color == "d73a4a"

    def test_github_label_minimal(self) -> None:
        """Test GitHubLabel with minimal fields."""
        label = GitHubLabel(id=2, name="enhancement")
        assert label.name == "enhancement"
        assert label.color == "default"


class TestGitHubMilestone:
    """Tests for GitHubMilestone model."""

    def test_github_milestone_basic(self) -> None:
        """Test basic GitHubMilestone instantiation."""
        milestone = GitHubMilestone(
            id=1,
            number=1,
            title="v1.0",
            state="open",
        )
        assert milestone.id == 1
        assert milestone.number == 1
        assert milestone.title == "v1.0"
        assert milestone.state == "open"


class TestGitHubIssue:
    """Tests for GitHubIssue model."""

    def test_github_issue_basic(self) -> None:
        """Test basic GitHubIssue instantiation."""
        now = utcnow()
        user = GitHubUser(id=1, login="testuser", type="User")
        issue = GitHubIssue(
            id=1,
            number=42,
            title="Test Issue",
            body="This is a test issue",
            state="open",
            labels=[],
            assignees=[],
            milestone=None,
            comments_count=5,
            created_at=now,
            updated_at=now,
            closed_at=None,
            user=user,
            url="https://api.github.com/repos/owner/repo/issues/42",
            html_url="https://github.com/owner/repo/issues/42",
            repository="owner/repo",
        )
        assert issue.id == 1
        assert issue.number == 42
        assert issue.title == "Test Issue"
        assert issue.state == "open"
        assert issue.repository == "owner/repo"

    def test_github_issue_with_labels(self) -> None:
        """Test GitHubIssue with labels."""
        now = utcnow()
        user = GitHubUser(id=1, login="testuser", type="User")
        label1 = GitHubLabel(id=1, name="bug", color="d73a4a")
        label2 = GitHubLabel(id=2, name="priority", color="ff7b00")

        issue = GitHubIssue(
            id=1,
            number=1,
            title="Bug report",
            body="Bug description",
            state="open",
            labels=[label1, label2],
            assignees=[],
            milestone=None,
            comments_count=0,
            created_at=now,
            updated_at=now,
            user=user,
            url="https://api.github.com/repos/owner/repo/issues/1",
            html_url="https://github.com/owner/repo/issues/1",
            repository="owner/repo",
        )
        assert len(issue.labels) == 2
        assert issue.labels[0].name == "bug"
        assert issue.labels[1].name == "priority"

    def test_github_issue_closed(self) -> None:
        """Test GitHubIssue with closed state."""
        now = utcnow()
        user = GitHubUser(id=1, login="testuser", type="User")

        issue = GitHubIssue(
            id=1,
            number=1,
            title="Closed issue",
            body="This is closed",
            state="closed",
            labels=[],
            assignees=[],
            milestone=None,
            comments_count=3,
            created_at=now,
            updated_at=now,
            closed_at=now,
            user=user,
            url="https://api.github.com/repos/owner/repo/issues/1",
            html_url="https://github.com/owner/repo/issues/1",
            repository="owner/repo",
        )
        assert issue.state == "closed"
        assert issue.closed_at is not None


class TestGitHubComment:
    """Tests for GitHubComment model."""

    def test_github_comment_basic(self) -> None:
        """Test basic GitHubComment instantiation."""
        now = utcnow()
        user = GitHubUser(id=1, login="commenter", type="User")
        comment = GitHubComment(
            id=12345,
            body="This is a comment",
            user=user,
            created_at=now,
            updated_at=now,
            issue_number=42,
            html_url="https://github.com/owner/repo/issues/42#issuecomment-12345",
        )
        assert comment.id == 12345
        assert comment.body == "This is a comment"
        assert comment.issue_number == 42
        assert comment.discussion_number is None

    def test_github_comment_discussion(self) -> None:
        """Test GitHubComment for discussion."""
        now = utcnow()
        user = GitHubUser(id=1, login="commenter", type="User")
        comment = GitHubComment(
            id=67890,
            body="Discussion comment",
            user=user,
            created_at=now,
            updated_at=now,
            discussion_number=5,
        )
        assert comment.discussion_number == 5
        assert comment.issue_number is None


class TestGitHubDiscussion:
    """Tests for GitHubDiscussion model."""

    def test_github_discussion_basic(self) -> None:
        """Test basic GitHubDiscussion instantiation."""
        now = utcnow()
        author = GitHubUser(id=1, login="discusser", type="User")
        category = GitHubDiscussionCategory(id="DIC_kwDO", name="Q&A", slug="q-a")

        discussion = GitHubDiscussion(
            id="D_kwDO",
            number=1,
            title="How to do X?",
            body="I want to know how to do X",
            category=category,
            answer_id=None,
            upvote_count=5,
            comments_count=3,
            author=author,
            created_at=now,
            updated_at=now,
            url="https://github.com/owner/repo/discussions/1",
            repository="owner/repo",
        )
        assert discussion.id == "D_kwDO"
        assert discussion.number == 1
        assert discussion.title == "How to do X?"
        assert discussion.category.name == "Q&A"
        assert discussion.upvote_count == 5

    def test_github_discussion_with_answer(self) -> None:
        """Test GitHubDiscussion with an answer."""
        now = utcnow()
        author = GitHubUser(id=1, login="discusser", type="User")
        category = GitHubDiscussionCategory(id="DIC_kwDO", name="Q&A", slug="q-a")

        discussion = GitHubDiscussion(
            id="D_kwDO",
            number=1,
            title="Answered question",
            body="Question body",
            category=category,
            answer_id="DC_kwDO",
            upvote_count=10,
            comments_count=5,
            author=author,
            created_at=now,
            updated_at=now,
            url="https://github.com/owner/repo/discussions/1",
            repository="owner/repo",
        )
        assert discussion.answer_id == "DC_kwDO"


class TestGitHubRepository:
    """Tests for GitHubRepository model."""

    def test_github_repository_basic(self) -> None:
        """Test basic GitHubRepository instantiation."""
        repo = GitHubRepository(
            id=12345,
            owner="testowner",
            name="testrepo",
            full_name="testowner/testrepo",
            description="A test repository",
            topics=["python", "testing"],
            has_issues=True,
            has_discussions=True,
            permissions={"admin": True, "push": True, "pull": True},
            html_url="https://github.com/testowner/testrepo",
            is_private=False,
        )
        assert repo.id == 12345
        assert repo.full_name == "testowner/testrepo"
        assert repo.has_issues is True
        assert repo.has_discussions is True
        assert "python" in repo.topics

    def test_github_repository_no_discussions(self) -> None:
        """Test GitHubRepository without discussions."""
        repo = GitHubRepository(
            id=54321,
            owner="owner",
            name="repo",
            full_name="owner/repo",
            has_issues=True,
            has_discussions=False,
            html_url="https://github.com/owner/repo",
        )
        assert repo.has_discussions is False


class TestGitHubRateLimit:
    """Tests for GitHubRateLimit model."""

    def test_github_rate_limit_basic(self) -> None:
        """Test basic GitHubRateLimit instantiation."""
        reset_time = utcnow()
        rate_limit = GitHubRateLimit(
            limit=5000,
            remaining=4999,
            reset=reset_time,
            used=1,
        )
        assert rate_limit.limit == 5000
        assert rate_limit.remaining == 4999
        assert rate_limit.reset == reset_time

    def test_github_rate_limit_defaults(self) -> None:
        """Test GitHubRateLimit with defaults."""
        reset_time = utcnow()
        rate_limit = GitHubRateLimit(reset=reset_time)
        assert rate_limit.limit == 5000
        assert rate_limit.remaining == 5000
        assert rate_limit.used == 0


class TestGitHubWebhookEvent:
    """Tests for GitHubWebhookEvent model."""

    def test_github_webhook_event_basic(self) -> None:
        """Test basic GitHubWebhookEvent instantiation."""
        event = GitHubWebhookEvent(
            delivery_id="12345678-1234-1234-1234-123456789012",
            event_type="issues",
            action="opened",
            payload={"issue": {"number": 1}},
            repository="owner/repo",
            sender="testuser",
        )
        assert event.delivery_id == "12345678-1234-1234-1234-123456789012"
        assert event.event_type == "issues"
        assert event.action == "opened"
        assert event.repository == "owner/repo"


class TestGitHubAuthType:
    """Tests for GitHubAuthType enum."""

    def test_github_auth_type_values(self) -> None:
        """Test GitHubAuthType enum values."""
        assert GitHubAuthType.OAUTH.value == "oauth"
        assert GitHubAuthType.APP_INSTALLATION.value == "app_installation"


class TestGitHubAppInstallation:
    """Tests for GitHubAppInstallation model."""

    def test_github_app_installation_basic(self) -> None:
        """Test basic GitHubAppInstallation instantiation."""
        now = utcnow()
        account = GitHubUser(id=1, login="testorg", type="Organization")

        installation = GitHubAppInstallation(
            id=12345,
            account=account,
            repository_selection="all",
            permissions={"issues": "write", "discussions": "read"},
            events=["issues", "issue_comment"],
            created_at=now,
            updated_at=now,
        )
        assert installation.id == 12345
        assert installation.account.login == "testorg"
        assert installation.repository_selection == "all"
        assert "issues" in installation.events
