"""Tests for GitHub connector.

Plan 14-01: GitHub connector core with OAuth/App auth.
Per GITH-01: Test OAuth and GitHub App authentication.
Per GITH-09: Test rate limiting (5000 req/hr).
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from saw.connectors.github.connector import GitHubConnector, MockGithub
from saw.connectors.github.models import GitHubAuthType
from saw.connectors.protocol import AuthResult, ConnectorItem, AuthenticationError


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


@pytest.fixture
def mock_config() -> MagicMock:
    """Create mock connector config."""
    config = MagicMock()
    config.id = "test-connector-id"
    config.user_id = "test-user-id"
    config.platform = "github"
    config.config = {"access_token": "test-token"}
    config.credentials_encrypted = None
    return config


@pytest.fixture
def mock_rate_limiter() -> MagicMock:
    """Create mock rate limiter."""
    limiter = MagicMock()
    limiter.acquire = AsyncMock()
    return limiter


@pytest.fixture
def mock_session() -> MagicMock:
    """Create mock database session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


class TestGitHubConnector:
    """Tests for GitHubConnector class."""

    def test_platform_name(self) -> None:
        """Test platform_name returns 'github'."""
        assert GitHubConnector.platform_name == "github"

    def test_supports_push(self) -> None:
        """Test supports_push returns True."""
        assert GitHubConnector.supports_push is True

    @pytest.mark.asyncio
    async def test_authenticate_oauth(
        self,
        mock_config: MagicMock,
        mock_rate_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test OAuth authentication flow."""
        mock_oauth = MagicMock()
        mock_oauth.exchange_code = AsyncMock(return_value=(
            "encrypted-token",
            "test-user-id",
            {"user_info": {"login": "testuser"}},
        ))

        connector = GitHubConnector(
            config=mock_config,
            rate_limiter=mock_rate_limiter,
            session=mock_session,
            oauth_handler=mock_oauth,
        )

        result = await connector.authenticate({
            "oauth_code": "test-code",
            "state": "test-state",
        })

        assert isinstance(result, AuthResult)
        assert result.access_token == "encrypted-token"
        assert result.refresh_token is None  # GitHub OAuth doesn't use refresh

    @pytest.mark.asyncio
    async def test_authenticate_app_installation(
        self,
        mock_config: MagicMock,
        mock_rate_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test GitHub App installation authentication."""
        mock_app = MagicMock()
        mock_app.get_installation_token = AsyncMock()
        mock_app.get_installation_token.return_value = MagicMock(
            token="installation-token",
            expires_at=utcnow(),
            repositories=[123, 456],
            permissions={"issues": "write"},
        )
        mock_app.encrypt_token = MagicMock(return_value="encrypted-installation-token")

        connector = GitHubConnector(
            config=mock_config,
            rate_limiter=mock_rate_limiter,
            session=mock_session,
            app_handler=mock_app,
        )

        result = await connector.authenticate({
            "installation_id": 12345,
        })

        assert isinstance(result, AuthResult)
        assert "encrypted" in result.access_token

    @pytest.mark.asyncio
    async def test_authenticate_missing_credentials(
        self,
        mock_config: MagicMock,
        mock_rate_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test authentication with missing credentials raises error."""
        connector = GitHubConnector(
            config=mock_config,
            rate_limiter=mock_rate_limiter,
            session=mock_session,
        )

        with pytest.raises(AuthenticationError):
            await connector.authenticate({})

    @pytest.mark.asyncio
    async def test_get_items_returns_items_from_selected_repos(
        self,
        mock_config: MagicMock,
        mock_rate_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test get_items returns items from selected repositories."""
        connector = GitHubConnector(
            config=mock_config,
            rate_limiter=mock_rate_limiter,
            session=mock_session,
        )

        # Create mock item
        mock_item = ConnectorItem(
            id="test-item",
            title="Test Issue",
            content="Test content",
        )

        # Create mock repo config
        mock_repo_config = MagicMock()
        mock_repo_config.repository_id = "owner/repo"
        mock_repo_config.sync_issues = True
        mock_repo_config.sync_discussions = False

        # Patch internal methods
        async def mock_ensure():
            connector._client = MockGithub()

        async def mock_load_repos():
            connector._selected_repositories = [mock_repo_config]
            return [mock_repo_config]

        async def mock_load_cursors():
            connector._sync_cursors = {}
            return {}

        async def mock_fetch_issues(repo_id, since, filters):
            return [mock_item]

        with patch.object(connector, '_ensure_client', side_effect=mock_ensure):
            with patch.object(connector, '_load_selected_repositories', side_effect=mock_load_repos):
                with patch.object(connector, '_load_sync_cursors', side_effect=mock_load_cursors):
                    with patch.object(connector, '_fetch_issues', side_effect=mock_fetch_issues):
                        items = await connector.get_items()

                        assert len(items) == 1
                        assert items[0].title == "Test Issue"

    @pytest.mark.asyncio
    async def test_rate_limiter_enforced(
        self,
        mock_config: MagicMock,
        mock_rate_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test rate limiter is acquired before API calls."""
        # The rate limiter is used in _ensure_client, _fetch_issues, check_rate_limit
        # This test verifies the rate limiter interface is correct
        connector = GitHubConnector(
            config=mock_config,
            rate_limiter=mock_rate_limiter,
            session=mock_session,
        )

        # Directly test that rate limiter would be called in check_rate_limit
        connector._client = MockGithub()

        # When check_rate_limit is called, it should use rate limiter
        await connector.check_rate_limit()

        # Rate limiter should be called
        assert mock_rate_limiter.acquire.call_count >= 1

    @pytest.mark.asyncio
    async def test_transform_to_claim(
        self,
        mock_config: MagicMock,
        mock_rate_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test transform_to_claim produces correct claim dict."""
        connector = GitHubConnector(
            config=mock_config,
            rate_limiter=mock_rate_limiter,
            session=mock_session,
        )

        item = ConnectorItem(
            id="github-issue-owner/repo#42",
            title="Test Issue",
            content="Issue body content",
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
                "labels": ["bug", "priority"],
            },
        )

        claim = connector.transform_to_claim(item)

        assert claim["title"] == "Test Issue"
        assert claim["content"] == "Issue body content"
        assert claim["source_platform"] == "github"
        assert claim["source_id"] == "github-issue-owner/repo#42"
        assert claim["metadata"]["github_repository"] == "owner/repo"

    @pytest.mark.asyncio
    async def test_transform_from_claim(
        self,
        mock_config: MagicMock,
        mock_rate_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test transform_from_claim produces correct ConnectorItem."""
        connector = GitHubConnector(
            config=mock_config,
            rate_limiter=mock_rate_limiter,
            session=mock_session,
        )

        claim = {
            "title": "Test Comment",
            "content": "Comment body",
            "source_id": "github-comment-123",
            "source_url": "https://github.com/owner/repo/issues/42#issuecomment-123",
            "metadata": {
                "github_repository": "owner/repo",
                "github_type": "issue",
                "github_issue_number": 42,
            },
        }

        item = connector.transform_from_claim(claim)

        assert item.content == "Comment body"
        assert item.metadata["repository"] == "owner/repo"
        assert item.metadata["parent_type"] == "issue"

    @pytest.mark.asyncio
    async def test_check_rate_limit(
        self,
        mock_config: MagicMock,
        mock_rate_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test check_rate_limit returns current status."""
        connector = GitHubConnector(
            config=mock_config,
            rate_limiter=mock_rate_limiter,
            session=mock_session,
        )

        with patch.object(connector, '_ensure_client') as mock_ensure:
            mock_ensure.return_value = MockGithub()

            rate_limit = await connector.check_rate_limit()

            assert rate_limit.limit == 5000
            assert rate_limit.remaining >= 0

    @pytest.mark.asyncio
    async def test_put_item_posts_comment(
        self,
        mock_config: MagicMock,
        mock_rate_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test put_item creates comment on issue."""
        connector = GitHubConnector(
            config=mock_config,
            rate_limiter=mock_rate_limiter,
            session=mock_session,
        )

        # Set up mock client
        mock_github = MockGithub()
        mock_repo = mock_github.get_repo("owner/repo")

        # Add get_issue mock
        mock_issue = MagicMock()
        mock_issue.create_comment = MagicMock(return_value=MagicMock(id=999))
        mock_repo.get_issue = MagicMock(return_value=mock_issue)

        connector._client = mock_github
        connector._access_token = "test-token"

        item = ConnectorItem(
            id="",
            title="",
            content="Test comment",
            metadata={
                "parent_type": "issue",
                "parent_number": 42,
                "repository": "owner/repo",
            },
        )

        with patch.object(mock_github, 'get_repo', return_value=mock_repo):
            comment_id = await connector.put_item(item)

            assert "github-comment" in comment_id

    @pytest.mark.asyncio
    async def test_delete_item_returns_false(
        self,
        mock_config: MagicMock,
        mock_rate_limiter: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test delete_item returns False (not supported)."""
        connector = GitHubConnector(
            config=mock_config,
            rate_limiter=mock_rate_limiter,
            session=mock_session,
        )

        result = await connector.delete_item("test-id")
        assert result is False


class TestMockGithub:
    """Tests for MockGithub helper class."""

    def test_get_repo_creates_mock(self) -> None:
        """Test get_repo creates mock repo."""
        client = MockGithub()
        repo = client.get_repo("owner/repo")

        assert repo.full_name == "owner/repo"
        assert repo.has_issues is True

    def test_get_rate_limit_returns_mock(self) -> None:
        """Test get_rate_limit returns mock limit."""
        client = MockGithub()
        limit = client.get_rate_limit()

        assert limit.core.limit == 5000
        assert limit.core.remaining == 5000
