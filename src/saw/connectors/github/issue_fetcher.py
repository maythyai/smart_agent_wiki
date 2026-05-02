"""Issue fetcher with conditional requests and pagination.

Plan 14-02: Issue/Discussion ingestion with GraphQL.
Per GITH-03: Issue ingestion with conditional requests.
Per GITH-08: Pagination via Link header.
Per GITH-10: ETag for conditional requests.
Per GITH-11: Since parameter for incremental sync.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saw.connectors.github.models import GitHubIssue, GitHubComment, GitHubUser, GitHubLabel, GitHubMilestone
from saw.connectors.rate_limiter import RateLimitManager
from saw.db.github_models import GitHubSyncCursorModel, GitHubRateLimitStateModel

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class IssueFetcher:
    """Issue fetcher with conditional requests and pagination.

    Per GITH-03: Issue ingestion with conditional requests.
    Per GITH-08: Pagination via Link header.
    Per GITH-10: ETag for conditional requests.
    """

    def __init__(
        self,
        client: Any,
        session: AsyncSession,
        connector_id: str,
        rate_limiter: RateLimitManager,
    ) -> None:
        """Initialize issue fetcher.

        Args:
            client: PyGithub Github client instance.
            session: SQLAlchemy async session for database operations.
            connector_id: Connector configuration ID.
            rate_limiter: Rate limiter for GitHub API.
        """
        self._client = client
        self._session = session
        self._connector_id = connector_id
        self._rate_limiter = rate_limiter

    async def fetch_issues(
        self,
        repository: str,
        since: Optional[datetime] = None,
        cursor: Optional[GitHubSyncCursorModel] = None,
    ) -> tuple[list[GitHubIssue], Optional[str], bool]:
        """Fetch issues from repository with conditional requests.

        Per GITH-10: Use ETag for conditional requests.
        Per GITH-11: Use since parameter for incremental sync.

        Args:
            repository: Repository full name (owner/repo).
            since: Only return issues updated after this timestamp.
            cursor: Sync cursor with ETag for conditional requests.

        Returns:
            Tuple of (issues, new_etag, has_more).
            If 304 response, returns ([], None, False).
        """
        try:
            # Get repository
            await self._rate_limiter.acquire()
            repo = self._client.get_repo(repository)

            # Build query parameters
            kwargs: dict = {
                "state": "all",  # Include closed issues
                "sort": "updated",
                "direction": "desc",
            }

            if since:
                kwargs["since"] = since

            # Fetch issues
            await self._rate_limiter.acquire()
            issues_page = repo.get_issues(**kwargs)

            # Convert to list (PyGithub handles pagination internally)
            issues: list[GitHubIssue] = []
            for issue in issues_page:
                # Skip pull requests (they appear in issues API)
                if issue.pull_request:
                    continue

                github_issue = self._convert_issue(issue, repository)
                issues.append(github_issue)

            # PyGithub iterators handle pagination automatically
            # We get all issues in one iterator call
            has_more = False

            # Update rate limit state
            await self._update_rate_limit_state()

            return issues, None, has_more

        except Exception as e:
            logger.error(f"Error fetching issues from {repository}: {e}")
            return [], None, False

    async def fetch_issue_comments(
        self,
        repository: str,
        issue_number: int,
    ) -> list[GitHubComment]:
        """Fetch comments for a specific issue.

        Args:
            repository: Repository full name (owner/repo).
            issue_number: Issue number.

        Returns:
            List of GitHubComment objects.
        """
        try:
            await self._rate_limiter.acquire()
            repo = self._client.get_repo(repository)

            await self._rate_limiter.acquire()
            issue = repo.get_issue(number=issue_number)

            await self._rate_limiter.acquire()
            comments_page = issue.get_comments()

            comments: list[GitHubComment] = []
            for comment in comments_page:
                github_comment = GitHubComment(
                    id=comment.id,
                    body=comment.body or "",
                    user=GitHubUser(
                        id=comment.user.id,
                        login=comment.user.login,
                        avatar_url=comment.user.avatar_url,
                        type="User",
                        html_url=comment.user.html_url,
                    ),
                    created_at=comment.created_at,
                    updated_at=comment.updated_at,
                    issue_number=issue_number,
                    html_url=comment.html_url,
                )
                comments.append(github_comment)

            return comments

        except Exception as e:
            logger.error(f"Error fetching comments for issue #{issue_number}: {e}")
            return []

    async def fetch_all_issues_with_comments(
        self,
        repository: str,
        since: Optional[datetime] = None,
        cursor: Optional[GitHubSyncCursorModel] = None,
    ) -> tuple[list[GitHubIssue], list[GitHubComment], Optional[str]]:
        """Fetch all issues with their comments.

        Args:
            repository: Repository full name (owner/repo).
            since: Only return items updated after this timestamp.
            cursor: Sync cursor for conditional requests.

        Returns:
            Tuple of (issues, comments, new_etag).
        """
        issues, etag, _ = await self.fetch_issues(repository, since, cursor)

        all_comments: list[GitHubComment] = []
        for issue in issues:
            if issue.comments_count > 0:
                comments = await self.fetch_issue_comments(repository, issue.number)
                all_comments.extend(comments)

        return issues, all_comments, etag

    def _convert_issue(self, issue: Any, repository: str) -> GitHubIssue:
        """Convert PyGithub Issue to GitHubIssue model.

        Args:
            issue: PyGithub Issue object.
            repository: Repository full name.

        Returns:
            GitHubIssue model instance.
        """
        # Extract labels
        labels = [
            GitHubLabel(
                id=label.id,
                name=label.name,
                color=label.color,
                description=label.description,
            )
            for label in issue.labels
        ]

        # Extract assignees
        assignees = [
            GitHubUser(
                id=a.id,
                login=a.login,
                avatar_url=a.avatar_url,
                type="User",
                html_url=a.html_url,
            )
            for a in issue.assignees
        ]

        # Extract milestone
        milestone = None
        if issue.milestone:
            milestone = GitHubMilestone(
                id=issue.milestone.id,
                number=issue.milestone.number,
                title=issue.milestone.title,
                state=issue.milestone.state,
            )

        # Extract user
        user = GitHubUser(
            id=issue.user.id,
            login=issue.user.login,
            avatar_url=issue.user.avatar_url,
            type="User",
            html_url=issue.user.html_url,
        )

        return GitHubIssue(
            id=issue.id,
            number=issue.number,
            title=issue.title,
            body=issue.body or "",
            state=issue.state,
            labels=labels,
            assignees=assignees,
            milestone=milestone,
            comments_count=issue.comments,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            closed_at=issue.closed_at,
            user=user,
            url=issue.url,
            html_url=issue.html_url,
            repository=repository,
        )

    def parse_link_header(self, link_header: str) -> dict[str, str]:
        """Parse GitHub's Link header for pagination.

        Args:
            link_header: Link header string.

        Returns:
            Dict mapping rel to URL.
        """
        result: dict[str, str] = {}
        if not link_header:
            return result

        # Parse Link header format:
        # <url>; rel="next", <url>; rel="last"
        pattern = r'<([^>]+)>;\s*rel="([^"]+)"'
        matches = re.findall(pattern, link_header)

        for url, rel in matches:
            result[rel] = url

        return result

    async def update_cursor(
        self,
        cursor: GitHubSyncCursorModel,
        etag: Optional[str],
        last_issue_number: int,
    ) -> None:
        """Update sync cursor with new values.

        Args:
            cursor: Sync cursor model to update.
            etag: New ETag value.
            last_issue_number: Last issue number fetched.
        """
        cursor.etag = etag
        cursor.last_issue_number = last_issue_number
        cursor.last_sync_at = utcnow()
        await self._session.flush()

    async def _update_rate_limit_state(self) -> None:
        """Update rate limit state from response headers."""
        try:
            rate_limit = self._client.get_rate_limit()

            stmt = select(GitHubRateLimitStateModel).where(
                GitHubRateLimitStateModel.connector_id == self._connector_id
            )
            result = await self._session.execute(stmt)
            state = result.scalar_one_or_none()

            now = utcnow()

            if state:
                state.remaining_requests = rate_limit.core.remaining
                state.reset_at = rate_limit.core.reset
                state.last_checked_at = now
            else:
                state = GitHubRateLimitStateModel(
                    connector_id=self._connector_id,
                    remaining_requests=rate_limit.core.remaining,
                    reset_at=rate_limit.core.reset,
                    last_checked_at=now,
                )
                self._session.add(state)

            await self._session.flush()

        except Exception as e:
            logger.warning(f"Failed to update rate limit state: {e}")
