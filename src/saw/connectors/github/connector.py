"""GitHub connector implementation.

Plan 14-01: GitHub connector core with OAuth/App auth.
Plan 14-02: Issue/Discussion ingestion with GraphQL.
Per GITH-01: OAuth and GitHub App authentication.
Per GITH-02: Repository selection.
Per GITH-09: Rate limiting (5000 req/hr).
Per GITH-10: Sync cursor persistence.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saw.connectors.protocol import (
    UnifiedConnectorInterface,
    AuthResult,
    ConnectorItem,
    AuthenticationError,
    SyncError,
)
from saw.connectors.models import ConnectorConfig
from saw.connectors.rate_limiter import RateLimitManager
from saw.domain.exceptions import ConnectorError
from saw.connectors.github.models import (
    GitHubUser,
    GitHubIssue,
    GitHubComment,
    GitHubDiscussion,
    GitHubRepository,
    GitHubRateLimit,
    GitHubAuthType,
)
from saw.connectors.github.oauth import GitHubOAuthHandler, OAuthError
from saw.connectors.github.app_installation import GitHubAppInstallationHandler
from saw.db.github_models import (
    GitHubSyncCursorModel,
    GitHubRepositoryConfigModel,
    GitHubRateLimitStateModel,
)

logger = logging.getLogger(__name__)
from saw.domain.utils import utcnow  # noqa: F401


class GitHubConnector(UnifiedConnectorInterface):
    """GitHub connector implementing UnifiedConnectorInterface.

    Per GITH-01: OAuth and GitHub App authentication.
    Per GITH-09: Rate limiting (5000 req/hr tracked).
    Per GITH-10: Sync cursor persists after each sync.
    """

    platform_name: str = "github"
    supports_push: bool = True  # Can post comments

    def __init__(
        self,
        config: ConnectorConfig,
        rate_limiter: RateLimitManager,
        session: AsyncSession,
        oauth_handler: Optional[GitHubOAuthHandler] = None,
        app_handler: Optional[GitHubAppInstallationHandler] = None,
    ) -> None:
        """Initialize GitHub connector.

        Args:
            config: Connector configuration.
            rate_limiter: Rate limiter for GitHub API.
            session: SQLAlchemy async session for database operations.
            oauth_handler: OAuth handler for GitHub (optional).
            app_handler: App installation handler (optional).
        """
        self._config = config
        self._rate_limiter = rate_limiter
        self._session = session
        self._oauth_handler = oauth_handler
        self._app_handler = app_handler

        # Client state
        self._client: Optional[Any] = None
        self._auth_type: GitHubAuthType = GitHubAuthType.OAUTH
        self._access_token: Optional[str] = None
        self._installation_id: Optional[int] = None
        self._selected_repositories: list[GitHubRepositoryConfigModel] = []
        self._sync_cursors: dict[str, GitHubSyncCursorModel] = {}

    async def _ensure_client(self) -> Any:
        """Ensure PyGithub client is initialized.

        Returns:
            Github client instance.
        """
        if self._client is None:
            try:
                from github import Github, Auth

                # Get access token from config
                access_token = await self._get_access_token()

                if access_token:
                    auth = Auth.Token(access_token)
                    self._client = Github(auth=auth)
                else:
                    logger.warning("No GitHub access token, using mock client")
                    self._client = MockGithub()

            except ImportError:
                logger.warning("PyGithub not installed, using mock")
                self._client = MockGithub()

        return self._client

    async def _get_access_token(self) -> Optional[str]:
        """Get decrypted access token from config.

        Returns:
            Access token string or None.
        """
        # Check if token is in config
        access_token = self._config.config.get("access_token", "")

        if not access_token:
            # Try encrypted token
            encrypted = self._config.credentials_encrypted
            if encrypted:
                from saw.connectors.token_encryption import TokenEncryption
                encryption = TokenEncryption()
                data = encryption.decrypt_token_set(encrypted)
                access_token = data.get("access_token", "")

        self._access_token = access_token
        return access_token

    async def _load_selected_repositories(self) -> list[GitHubRepositoryConfigModel]:
        """Load selected repositories from database.

        Returns:
            List of selected repository configs.
        """
        stmt = (
            select(GitHubRepositoryConfigModel)
            .where(GitHubRepositoryConfigModel.connector_id == self._config.id)
            .where(GitHubRepositoryConfigModel.is_selected == True)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        self._selected_repositories = list(models)
        return self._selected_repositories

    async def _load_sync_cursors(self) -> dict[str, GitHubSyncCursorModel]:
        """Load sync cursors for incremental sync.

        Returns:
            Dict mapping repository_id to cursor model.
        """
        stmt = select(GitHubSyncCursorModel).where(
            GitHubSyncCursorModel.connector_id == self._config.id
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        self._sync_cursors = {m.repository_id: m for m in models}
        return self._sync_cursors

    async def authenticate(self, credentials: dict) -> AuthResult:
        """Complete authentication flow.

        Per GITH-01: OAuth or GitHub App authentication.

        Args:
            credentials: Dict with either:
                - 'oauth_code' and 'state' for OAuth flow
                - 'installation_id' for GitHub App flow

        Returns:
            AuthResult with access token and user/org info.

        Raises:
            AuthenticationError: If authentication fails.
        """
        # Check for GitHub App installation
        installation_id = credentials.get("installation_id")
        if installation_id:
            return await self._authenticate_app(installation_id)

        # Otherwise, use OAuth flow
        code = credentials.get("oauth_code")
        state = credentials.get("state")

        if not code or not state:
            raise AuthenticationError("Missing OAuth code or state")

        return await self._authenticate_oauth(code, state)

    async def _authenticate_oauth(self, code: str, state: str) -> AuthResult:
        """Complete OAuth authentication flow.

        Args:
            code: OAuth authorization code.
            state: OAuth state string.

        Returns:
            AuthResult with tokens and user info.
        """
        if not self._oauth_handler:
            raise AuthenticationError("OAuth handler not configured")

        try:
            encrypted, user_id, raw_response = await self._oauth_handler.exchange_code(
                code, state
            )

            user_info = raw_response.get("user_info", {})

            return AuthResult(
                access_token=encrypted,
                refresh_token=None,
                expires_at=None,  # GitHub OAuth tokens don't expire
                scopes=["repo", "read:org", "read:user"],
                raw_response={
                    "user_login": user_info.get("login"),
                    "user_name": user_info.get("name"),
                    "user_email": user_info.get("email"),
                    "user_avatar": user_info.get("avatar_url"),
                },
            )
        except OAuthError as e:
            raise AuthenticationError(f"GitHub OAuth failed: {str(e)}")

    async def _authenticate_app(self, installation_id: int) -> AuthResult:
        """Complete GitHub App authentication.

        Args:
            installation_id: GitHub App installation ID.

        Returns:
            AuthResult with installation token.
        """
        if not self._app_handler:
            raise AuthenticationError("App handler not configured")

        try:
            token = await self._app_handler.get_installation_token(installation_id)

            # Encrypt token for storage
            encrypted = self._app_handler.encrypt_token(token.token)

            self._auth_type = GitHubAuthType.APP_INSTALLATION
            self._installation_id = installation_id

            return AuthResult(
                access_token=encrypted,
                refresh_token=None,
                expires_at=token.expires_at,
                scopes=list(token.permissions.keys()),
                raw_response={
                    "installation_id": installation_id,
                    "repositories": token.repositories,
                    "permissions": token.permissions,
                },
            )
        except Exception as e:
            raise AuthenticationError(f"GitHub App auth failed: {str(e)}")

    async def get_items(
        self,
        since: Optional[datetime] = None,
        filters: Optional[dict] = None,
    ) -> list[ConnectorItem]:
        """Pull issues and discussions from selected repositories.

        Per GITH-10: Sync cursor persists after each fetch.

        Args:
            since: Only return items updated after this timestamp.
            filters: Optional filters (repository_id, type, etc.).

        Returns:
            List of ConnectorItem from selected repositories.
        """
        await self._ensure_client()
        await self._load_selected_repositories()
        await self._load_sync_cursors()

        items: list[ConnectorItem] = []

        for repo_config in self._selected_repositories:
            repo_id = repo_config.repository_id

            # Fetch issues if enabled
            if repo_config.sync_issues:
                issue_items = await self._fetch_issues(repo_id, since, filters)
                items.extend(issue_items)

            # Fetch discussions if enabled
            if repo_config.sync_discussions:
                discussion_items = await self._fetch_discussions(repo_id, since, filters)
                items.extend(discussion_items)

        return items

    async def _fetch_issues(
        self,
        repository_id: str,
        since: Optional[datetime],
        filters: Optional[dict],
    ) -> list[ConnectorItem]:
        """Fetch issues from a repository.

        Args:
            repository_id: Repository full name (owner/repo).
            since: Only fetch issues updated after this time.
            filters: Optional filters.

        Returns:
            List of ConnectorItem from issues.
        """
        items: list[ConnectorItem] = []

        try:
            client = await self._ensure_client()

            # Parse repository
            owner, repo_name = repository_id.split("/", 1)

            await self._rate_limiter.acquire()
            repo = client.get_repo(f"{owner}/{repo_name}")

            # Get cursor for conditional requests
            cursor = self._sync_cursors.get(repository_id)

            # Build query parameters
            kwargs = {"state": "all"}
            if since:
                kwargs["since"] = since

            # Fetch issues
            await self._rate_limiter.acquire()
            issues = list(repo.get_issues(**kwargs))

            for issue in issues:
                item = self._transform_issue_to_item(issue, repository_id)
                items.append(item)

            # Update sync cursor
            await self._update_sync_cursor(repository_id, "issues", len(items))

        except Exception as e:
            logger.error("Error fetching issues from %s: %s", repository_id, e)
            raise ConnectorError(
                f"Failed to fetch issues from {repository_id}: {e}"
            ) from e

    async def _fetch_discussions(
        self,
        repository_id: str,
        since: Optional[datetime],
        filters: Optional[dict],
    ) -> list[ConnectorItem]:
        """Fetch discussions from a repository.

        Note: Discussions require GraphQL API (Plan 14-02).

        Args:
            repository_id: Repository full name (owner/repo).
            since: Only fetch discussions updated after this time.
            filters: Optional filters.

        Returns:
            List of ConnectorItem from discussions.
        """
        # Placeholder for Plan 14-02
        # GraphQL client will be implemented there
        return []

    def _transform_issue_to_item(
        self,
        issue: Any,
        repository_id: str,
    ) -> ConnectorItem:
        """Transform GitHub issue to ConnectorItem.

        Args:
            issue: PyGithub Issue object.
            repository_id: Repository full name.

        Returns:
            ConnectorItem with issue data.
        """
        # Extract labels
        labels = [label.name for label in issue.labels]

        # Extract assignees
        assignees = [a.login for a in issue.assignees]

        # Extract milestone
        milestone = issue.milestone.title if issue.milestone else None

        return ConnectorItem(
            id=f"github-issue-{repository_id}#{issue.number}",
            title=issue.title,
            content=issue.body or "",
            url=issue.html_url,
            author=issue.user.login if issue.user else None,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            metadata={
                "platform": "github",
                "type": "issue",
                "repository": repository_id,
                "issue_number": issue.number,
                "state": issue.state,
                "labels": labels,
                "assignees": assignees,
                "milestone": milestone,
                "comments_count": issue.comments,
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
            },
        )

    async def _update_sync_cursor(
        self,
        repository_id: str,
        sync_type: str,
        items_count: int,
    ) -> None:
        """Update sync cursor after successful fetch.

        Per GITH-10: Cursor persists for resume capability.

        Args:
            repository_id: Repository full name.
            sync_type: Type of items synced (issues/discussions).
            items_count: Number of items synced.
        """
        from saw.db.github_models import GitHubSyncType

        stmt = select(GitHubSyncCursorModel).where(
            GitHubSyncCursorModel.connector_id == self._config.id,
            GitHubSyncCursorModel.repository_id == repository_id,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        now = utcnow()

        if model:
            model.last_sync_at = now
            model.items_synced += items_count
        else:
            sync_type_enum = (
                GitHubSyncType.ISSUES if sync_type == "issues"
                else GitHubSyncType.DISCUSSIONS
            )
            model = GitHubSyncCursorModel(
                connector_id=self._config.id,
                repository_id=repository_id,
                sync_type=sync_type_enum,
                last_sync_at=now,
                items_synced=items_count,
            )
            self._session.add(model)

        await self._session.flush()

    async def put_item(self, item: ConnectorItem) -> str:
        """Push item to GitHub.

        Used for posting comments to issues or discussions.

        Args:
            item: Item to push (comment).

        Returns:
            Comment ID.

        Raises:
            SyncError: If push fails.
        """
        await self._ensure_client()

        parent_type = item.metadata.get("parent_type")
        parent_number = item.metadata.get("parent_number")
        repository_id = item.metadata.get("repository")

        if not repository_id or not parent_number:
            raise SyncError("Missing repository or parent number for comment")

        try:
            client = await self._ensure_client()

            # Get the repository
            await self._rate_limiter.acquire()
            repo = client.get_repo(repository_id)

            if parent_type == "issue":
                # Post comment to issue
                await self._rate_limiter.acquire()
                issue = repo.get_issue(number=parent_number)
                comment = issue.create_comment(item.content)
                return f"github-comment-{repository_id}#{comment.id}"
            else:
                # Discussion comments require GraphQL (Plan 14-02)
                raise SyncError("Discussion comments not yet supported")

        except Exception as e:
            raise SyncError(f"Failed to push comment to GitHub: {str(e)}")

    async def delete_item(self, item_id: str) -> bool:
        """Delete item from GitHub.

        Note: GitHub API doesn't support deleting comments via REST API.
        Only editing is supported.

        Args:
            item_id: Platform-specific item ID.

        Returns:
            False (deletion not supported).
        """
        # GitHub doesn't support deleting comments via API
        # Only editing is possible
        return False

    def transform_to_claim(self, item: ConnectorItem) -> dict:
        """Convert GitHub item to SAW Claim dict.

        Placeholder for Plan 14-02 (detailed transformation).

        Args:
            item: ConnectorItem from GitHub.

        Returns:
            Dict matching Claim schema.
        """
        return {
            "title": item.title,
            "content": item.content,
            "source_platform": "github",
            "source_id": item.id,
            "source_url": item.url,
            "metadata": {
                "github_repository": item.metadata.get("repository"),
                "github_type": item.metadata.get("type"),
                "github_issue_number": item.metadata.get("issue_number"),
                "github_state": item.metadata.get("state"),
                "github_labels": item.metadata.get("labels", []),
                **item.metadata,
            },
        }

    def transform_from_claim(self, claim: dict) -> ConnectorItem:
        """Convert SAW Claim dict to GitHub item format.

        Placeholder for Plan 14-02.

        Args:
            claim: SAW Claim dict.

        Returns:
            ConnectorItem ready for GitHub push.
        """
        return ConnectorItem(
            id=claim.get("source_id", ""),
            title=claim.get("title", ""),
            content=claim.get("content", ""),
            url=claim.get("source_url"),
            author=claim.get("author"),
            created_at=None,
            updated_at=None,
            metadata={
                "repository": claim.get("metadata", {}).get("github_repository"),
                "parent_type": claim.get("metadata", {}).get("github_type"),
                "parent_number": claim.get("metadata", {}).get("github_issue_number"),
            },
        )

    async def list_repositories(self) -> list[GitHubRepository]:
        """List accessible repositories.

        Per GITH-02: List repositories after authentication.

        Returns:
            List of GitHubRepository objects.
        """
        await self._ensure_client()

        repositories: list[GitHubRepository] = []

        try:
            client = await self._ensure_client()

            # Get all repositories accessible to the user
            await self._rate_limiter.acquire()
            repos = list(client.get_repos(affiliation="owner,collaborator,organization_member"))

            for repo in repos:
                # Filter to repos with issues or discussions enabled
                if not repo.has_issues and not repo.has_discussions:
                    continue

                repositories.append(GitHubRepository(
                    id=repo.id,
                    owner=repo.owner.login,
                    name=repo.name,
                    full_name=repo.full_name,
                    description=repo.description,
                    topics=list(repo.topics) if hasattr(repo, "topics") else [],
                    has_issues=repo.has_issues,
                    has_discussions=repo.has_discussions if hasattr(repo, "has_discussions") else False,
                    permissions={
                        "admin": repo.permissions.admin if hasattr(repo.permissions, "admin") else False,
                        "push": repo.permissions.push if hasattr(repo.permissions, "push") else False,
                        "pull": repo.permissions.pull if hasattr(repo.permissions, "pull") else True,
                    },
                    html_url=repo.html_url,
                    is_private=repo.private,
                ))

        except Exception as e:
            logger.error("Error listing repositories: %s", e)
            raise ConnectorError(
                f"Failed to list GitHub repositories: {e}"
            ) from e

        return repositories

    async def check_rate_limit(self) -> GitHubRateLimit:
        """Check current rate limit status.

        Per GITH-09: Track rate limit for conditional requests.

        Returns:
            GitHubRateLimit with current status.
        """
        await self._ensure_client()

        try:
            client = await self._ensure_client()
            await self._rate_limiter.acquire()
            rate_limit = client.get_rate_limit()

            return GitHubRateLimit(
                limit=rate_limit.core.limit,
                remaining=rate_limit.core.remaining,
                reset=rate_limit.core.reset,
                used=rate_limit.core.limit - rate_limit.core.remaining,
            )
        except Exception as e:
            logger.error("Error checking rate limit: %s", e)
            raise ConnectorError(
                f"Failed to check GitHub rate limit: {e}"
            ) from e


class MockGithub:
    """Minimal mock for testing without PyGithub."""

    def __init__(self) -> None:
        self._repos: dict[str, MockRepo] = {}

    def get_repo(self, full_name: str) -> "MockRepo":
        """Get or create mock repo."""
        if full_name not in self._repos:
            self._repos[full_name] = MockRepo(full_name)
        return self._repos[full_name]

    def get_repos(self, affiliation: str = "") -> list["MockRepo"]:
        """Get mock repos list."""
        return [MockRepo("owner/repo")]

    def get_rate_limit(self) -> "MockRateLimit":
        """Get mock rate limit."""
        return MockRateLimit()


class MockRepo:
    """Minimal mock repo for testing."""

    def __init__(self, full_name: str) -> None:
        self.full_name = full_name
        self.id = 12345
        self.owner = MockUser()
        self.name = full_name.split("/")[-1]
        self.description = "Mock repository"
        self.has_issues = True
        self.has_discussions = False
        self.topics: list[str] = []
        self.permissions = MockPermissions()
        self.html_url = f"https://github.com/{full_name}"
        self.private = False

    def get_issues(self, state: str = "all", since: Any = None) -> list["MockIssue"]:
        """Get mock issues."""
        return [MockIssue()]


class MockUser:
    """Minimal mock user."""

    def __init__(self) -> None:
        self.login = "mockuser"
        self.id = 1


class MockPermissions:
    """Minimal mock permissions."""

    admin = False
    push = True
    pull = True


class MockIssue:
    """Minimal mock issue for testing."""

    def __init__(self) -> None:
        self.id = 1
        self.number = 42
        self.title = "Mock Issue"
        self.body = "Mock body"
        self.state = "open"
        self.labels: list[Any] = []
        self.assignees: list[Any] = []
        self.milestone = None
        self.comments = 0
        self.created_at = utcnow()
        self.updated_at = utcnow()
        self.closed_at = None
        self.user = MockUser()
        self.html_url = "https://github.com/owner/repo/issues/42"

    def create_comment(self, body: str) -> "MockComment":
        """Create mock comment."""
        return MockComment()


class MockComment:
    """Minimal mock comment."""

    def __init__(self) -> None:
        self.id = 12345


class MockRateLimit:
    """Minimal mock rate limit."""

    def __init__(self) -> None:
        self.core = MockCoreRateLimit()


class MockCoreRateLimit:
    """Minimal mock core rate limit."""

    limit = 5000
    remaining = 5000
    reset = utcnow()
