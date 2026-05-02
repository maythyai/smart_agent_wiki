"""Tests for GitHub repository selector.

Plan 14-01: GitHub connector core with OAuth/App auth.
Per GITH-02: Repository selection persistence tests.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from saw.connectors.github.repository_selector import RepositorySelector
from saw.connectors.github.models import GitHubRepository
from saw.connectors.github.connector import GitHubConnector
from saw.db.github_models import GitHubRepositoryConfigModel


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


@pytest.fixture
def mock_connector() -> MagicMock:
    """Create mock GitHub connector."""
    connector = MagicMock(spec=GitHubConnector)
    connector.list_repositories = AsyncMock()
    return connector


@pytest.fixture
def mock_session() -> MagicMock:
    """Create mock database session."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    return session


class TestRepositorySelector:
    """Tests for RepositorySelector class."""

    @pytest.mark.asyncio
    async def test_list_accessible_repositories(
        self,
        mock_connector: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test listing accessible repositories."""
        mock_connector.list_repositories.return_value = [
            GitHubRepository(
                id=1,
                owner="owner1",
                name="repo1",
                full_name="owner1/repo1",
                has_issues=True,
                has_discussions=False,
                permissions={"push": True, "pull": True},
                html_url="https://github.com/owner1/repo1",
            ),
            GitHubRepository(
                id=2,
                owner="owner2",
                name="repo2",
                full_name="owner2/repo2",
                has_issues=True,
                has_discussions=True,
                permissions={"admin": True, "push": True},
                html_url="https://github.com/owner2/repo2",
            ),
            # No write permission
            GitHubRepository(
                id=3,
                owner="owner3",
                name="repo3",
                full_name="owner3/repo3",
                has_issues=True,
                has_discussions=False,
                permissions={"pull": True},
                html_url="https://github.com/owner3/repo3",
            ),
        ]

        selector = RepositorySelector(
            connector=mock_connector,
            session=mock_session,
            connector_id="test-connector",
        )

        repos = await selector.list_accessible_repositories()

        # Should only return repos with write access
        assert len(repos) == 2
        assert repos[0].full_name == "owner1/repo1"
        assert repos[1].full_name == "owner2/repo2"

    @pytest.mark.asyncio
    async def test_select_repositories(
        self,
        mock_connector: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test selecting repositories for sync."""
        mock_connector.list_repositories.return_value = [
            GitHubRepository(
                id=1,
                owner="owner1",
                name="repo1",
                full_name="owner1/repo1",
                has_issues=True,
                has_discussions=False,
                permissions={"push": True},
                html_url="https://github.com/owner1/repo1",
            ),
            GitHubRepository(
                id=2,
                owner="owner2",
                name="repo2",
                full_name="owner2/repo2",
                has_issues=True,
                has_discussions=True,
                permissions={"push": True},
                html_url="https://github.com/owner2/repo2",
            ),
        ]

        # Mock delete
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        selector = RepositorySelector(
            connector=mock_connector,
            session=mock_session,
            connector_id="test-connector",
        )

        selected, total = await selector.select_repositories(["owner1/repo1"])

        assert selected == 1
        assert total == 2

    @pytest.mark.asyncio
    async def test_select_repositories_validates_ids(
        self,
        mock_connector: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test selecting repositories validates IDs."""
        mock_connector.list_repositories.return_value = [
            GitHubRepository(
                id=1,
                owner="owner1",
                name="repo1",
                full_name="owner1/repo1",
                has_issues=True,
                has_discussions=False,
                permissions={"push": True},
                html_url="https://github.com/owner1/repo1",
            ),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        selector = RepositorySelector(
            connector=mock_connector,
            session=mock_session,
            connector_id="test-connector",
        )

        # Try to select invalid repo
        selected, total = await selector.select_repositories(["invalid/repo"])

        assert selected == 0
        assert total == 1

    @pytest.mark.asyncio
    async def test_get_selected_repositories(
        self,
        mock_connector: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test getting selected repositories."""
        mock_repo_config = MagicMock(spec=GitHubRepositoryConfigModel)
        mock_repo_config.repository_id = "owner/repo"
        mock_repo_config.repository_name = "repo"
        mock_repo_config.is_selected = True
        mock_repo_config.sync_issues = True
        mock_repo_config.sync_discussions = False

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_repo_config]
        mock_session.execute.return_value = mock_result

        selector = RepositorySelector(
            connector=mock_connector,
            session=mock_session,
            connector_id="test-connector",
        )

        repos = await selector.get_selected_repositories()

        assert len(repos) == 1
        assert repos[0].repository_id == "owner/repo"

    @pytest.mark.asyncio
    async def test_update_sync_settings(
        self,
        mock_connector: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test updating sync settings."""
        mock_repo_config = MagicMock(spec=GitHubRepositoryConfigModel)
        mock_repo_config.repository_id = "owner/repo"
        mock_repo_config.sync_issues = True
        mock_repo_config.sync_discussions = False
        mock_repo_config.sync_comments = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_repo_config
        mock_session.execute.return_value = mock_result

        selector = RepositorySelector(
            connector=mock_connector,
            session=mock_session,
            connector_id="test-connector",
        )

        success = await selector.update_sync_settings(
            "owner/repo",
            {"sync_discussions": True},
        )

        assert success is True
        assert mock_repo_config.sync_discussions is True

    @pytest.mark.asyncio
    async def test_update_sync_settings_not_found(
        self,
        mock_connector: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test updating sync settings for non-existent repo."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        selector = RepositorySelector(
            connector=mock_connector,
            session=mock_session,
            connector_id="test-connector",
        )

        success = await selector.update_sync_settings(
            "owner/notfound",
            {"sync_discussions": True},
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_deselect_repository(
        self,
        mock_connector: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test deselecting a repository."""
        mock_repo_config = MagicMock(spec=GitHubRepositoryConfigModel)
        mock_repo_config.repository_id = "owner/repo"
        mock_repo_config.is_selected = True

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_repo_config
        mock_session.execute.return_value = mock_result

        selector = RepositorySelector(
            connector=mock_connector,
            session=mock_session,
            connector_id="test-connector",
        )

        success = await selector.deselect_repository("owner/repo")

        assert success is True
        assert mock_repo_config.is_selected is False

    @pytest.mark.asyncio
    async def test_get_default_label_mapping(
        self,
        mock_connector: MagicMock,
        mock_session: MagicMock,
    ) -> None:
        """Test getting default label mapping."""
        selector = RepositorySelector(
            connector=mock_connector,
            session=mock_session,
            connector_id="test-connector",
        )

        mapping = await selector.get_default_label_mapping()

        assert mapping["bug"] == "bug"
        assert mapping["enhancement"] == "feature"
        assert mapping["documentation"] == "docs"
