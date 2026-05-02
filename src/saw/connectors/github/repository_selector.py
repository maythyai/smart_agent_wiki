"""Repository selection for GitHub connector.

Plan 14-01: GitHub connector core with OAuth/App auth.
Per GITH-02: Repository selection persistence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import logging

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from saw.connectors.github.models import GitHubRepository
from saw.connectors.github.connector import GitHubConnector
from saw.db.github_models import GitHubRepositoryConfigModel, GitHubSyncType

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class RepositorySelector:
    """Repository selection management for GitHub connector.

    Per GITH-02: Persist repository selection with sync preferences.
    """

    def __init__(
        self,
        connector: GitHubConnector,
        session: AsyncSession,
        connector_id: str,
    ) -> None:
        """Initialize repository selector.

        Args:
            connector: GitHubConnector instance for API calls.
            session: SQLAlchemy async session for database operations.
            connector_id: Connector configuration ID.
        """
        self._connector = connector
        self._session = session
        self._connector_id = connector_id

    async def list_accessible_repositories(self) -> list[GitHubRepository]:
        """List repositories accessible to the authenticated user.

        Returns repositories where user has write access and
        issues or discussions are enabled.

        Returns:
            List of GitHubRepository objects.
        """
        repositories = await self._connector.list_repositories()

        # Filter to repos with write permission
        writable = [
            repo for repo in repositories
            if repo.permissions.get("push", False) or repo.permissions.get("admin", False)
        ]

        # Filter to repos with issues or discussions
        valid_repos = [
            repo for repo in writable
            if repo.has_issues or repo.has_discussions
        ]

        return valid_repos

    async def select_repositories(
        self,
        repository_ids: list[str],
    ) -> tuple[int, int]:
        """Select repositories for sync.

        Persists repository selection to database. Clears previous selections.

        Args:
            repository_ids: List of repository full names (owner/repo).

        Returns:
            Tuple of (selected_count, total_accessible_count).
        """
        # Get accessible repositories
        accessible = await self.list_accessible_repositories()
        accessible_ids = {repo.full_name for repo in accessible}

        # Validate repository IDs
        valid_ids = [rid for rid in repository_ids if rid in accessible_ids]

        # Clear previous selections
        stmt = delete(GitHubRepositoryConfigModel).where(
            GitHubRepositoryConfigModel.connector_id == self._connector_id
        )
        await self._session.execute(stmt)

        # Insert new selections
        for repo_id in valid_ids:
            # Find repo info
            repo_info = next((r for r in accessible if r.full_name == repo_id), None)
            if repo_info:
                config = GitHubRepositoryConfigModel(
                    connector_id=self._connector_id,
                    repository_id=repo_id,
                    repository_name=repo_info.name,
                    is_selected=True,
                    sync_issues=repo_info.has_issues,
                    sync_discussions=repo_info.has_discussions,
                    sync_comments=True,
                    label_tag_mapping={},
                )
                self._session.add(config)

        await self._session.flush()

        return len(valid_ids), len(accessible)

    async def get_selected_repositories(self) -> list[GitHubRepositoryConfigModel]:
        """Get currently selected repositories.

        Returns:
            List of GitHubRepositoryConfigModel instances.
        """
        stmt = (
            select(GitHubRepositoryConfigModel)
            .where(GitHubRepositoryConfigModel.connector_id == self._connector_id)
            .where(GitHubRepositoryConfigModel.is_selected == True)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update_sync_settings(
        self,
        repository_id: str,
        settings: dict,
    ) -> bool:
        """Update sync settings for a repository.

        Args:
            repository_id: Repository full name (owner/repo).
            settings: Dict with sync_issues, sync_discussions, sync_comments, label_tag_mapping.

        Returns:
            True if updated, False if not found.
        """
        stmt = (
            select(GitHubRepositoryConfigModel)
            .where(GitHubRepositoryConfigModel.connector_id == self._connector_id)
            .where(GitHubRepositoryConfigModel.repository_id == repository_id)
        )
        result = await self._session.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            return False

        # Update settings
        if "sync_issues" in settings:
            config.sync_issues = settings["sync_issues"]
        if "sync_discussions" in settings:
            config.sync_discussions = settings["sync_discussions"]
        if "sync_comments" in settings:
            config.sync_comments = settings["sync_comments"]
        if "label_tag_mapping" in settings:
            config.label_tag_mapping = settings["label_tag_mapping"]

        await self._session.flush()
        return True

    async def deselect_repository(self, repository_id: str) -> bool:
        """Deselect a repository from sync.

        Args:
            repository_id: Repository full name (owner/repo).

        Returns:
            True if deselected, False if not found.
        """
        stmt = (
            select(GitHubRepositoryConfigModel)
            .where(GitHubRepositoryConfigModel.connector_id == self._connector_id)
            .where(GitHubRepositoryConfigModel.repository_id == repository_id)
        )
        result = await self._session.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            return False

        config.is_selected = False
        await self._session.flush()
        return True

    async def get_default_label_mapping(self) -> dict[str, str]:
        """Get default label to tag mapping.

        Returns:
            Dict mapping GitHub label names to SAW tag names.
        """
        return {
            "bug": "bug",
            "enhancement": "feature",
            "documentation": "docs",
            "question": "help",
            "wontfix": "wontfix",
            "duplicate": "duplicate",
            "good first issue": "good-first-issue",
            "help wanted": "help-wanted",
        }
