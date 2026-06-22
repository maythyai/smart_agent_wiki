"""GitHub GraphQL API client for Discussions.

Plan 14-02: Issue/Discussion ingestion with GraphQL.
Per GITH-04: Discussions require GraphQL API.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
import logging

import httpx

from saw.connectors.rate_limiter import RateLimitManager
from saw.connectors.github.models import (
    GitHubDiscussion,
    GitHubDiscussionCategory,
    GitHubComment,
    GitHubUser,
)

logger = logging.getLogger(__name__)
from saw.domain.utils import utcnow  # noqa: F401


# GraphQL queries
DISCUSSIONS_QUERY = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    discussions(first: 100, after: $cursor) {
      totalCount
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        id
        number
        title
        body
        category {
          id
          name
          slug
        }
        answer {
          id
        }
        upvoteCount
        comments(first: 100) {
          totalCount
          nodes {
            id
            body
            author {
              login
              avatarUrl
            }
            createdAt
            updatedAt
          }
        }
        author {
          login
          avatarUrl
        }
        createdAt
        updatedAt
        url
      }
    }
  }
}
"""

DISCUSSION_COMMENTS_QUERY = """
query($owner: String!, $repo: String!, $number: Int!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    discussion(number: $number) {
      comments(first: 100, after: $cursor) {
        totalCount
        pageInfo {
          hasNextPage
          endCursor
        }
        nodes {
          id
          body
          author {
            login
            avatarUrl
          }
          createdAt
          updatedAt
        }
      }
    }
  }
}
"""


class GitHubGraphQLClient:
    """GitHub GraphQL API client for Discussions.

    Per GITH-04: Discussions require GraphQL API.
    """

    GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

    def __init__(
        self,
        access_token: str,
        rate_limiter: RateLimitManager,
    ) -> None:
        """Initialize GraphQL client.

        Args:
            access_token: GitHub access token.
            rate_limiter: Rate limiter for API calls.
        """
        self._access_token = access_token
        self._rate_limiter = rate_limiter

    async def execute_query(
        self,
        query: str,
        variables: dict,
    ) -> dict:
        """Execute a GraphQL query.

        Args:
            query: GraphQL query string.
            variables: Query variables.

        Returns:
            Response data dict.

        Raises:
            GraphQLError: If query fails.
        """
        await self._rate_limiter.acquire()

        headers = {
            "Authorization": f"bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "query": query,
            "variables": variables,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.GITHUB_GRAPHQL_URL,
                headers=headers,
                json=payload,
                timeout=30.0,
            )

            if response.status_code != 200:
                raise GraphQLError(f"GraphQL request failed: {response.status_code}")

            data = response.json()

            if "errors" in data:
                errors = data["errors"]
                error_messages = [e.get("message", str(e)) for e in errors]
                raise GraphQLError(f"GraphQL errors: {'; '.join(error_messages)}")

            return data.get("data", {})

    async def query_discussions(
        self,
        owner: str,
        repo: str,
        cursor: Optional[str] = None,
    ) -> dict:
        """Query discussions from repository.

        Args:
            owner: Repository owner.
            repo: Repository name.
            cursor: Pagination cursor.

        Returns:
            Raw response data.
        """
        variables = {
            "owner": owner,
            "repo": repo,
            "cursor": cursor,
        }

        return await self.execute_query(DISCUSSIONS_QUERY, variables)

    async def query_discussion_comments(
        self,
        owner: str,
        repo: str,
        number: int,
        cursor: Optional[str] = None,
    ) -> dict:
        """Query comments for a specific discussion.

        Args:
            owner: Repository owner.
            repo: Repository name.
            number: Discussion number.
            cursor: Pagination cursor.

        Returns:
            Raw response data.
        """
        variables = {
            "owner": owner,
            "repo": repo,
            "number": number,
            "cursor": cursor,
        }

        return await self.execute_query(DISCUSSION_COMMENTS_QUERY, variables)


class GraphQLError(Exception):
    """GraphQL API error."""
    pass


class DiscussionFetcher:
    """Discussion fetcher using GraphQL API.

    Per GITH-04: Fetch discussions via GraphQL.
    """

    def __init__(
        self,
        graphql_client: GitHubGraphQLClient,
        session: Any,
        connector_id: str,
    ) -> None:
        """Initialize discussion fetcher.

        Args:
            graphql_client: GraphQL client instance.
            session: SQLAlchemy async session.
            connector_id: Connector configuration ID.
        """
        self._graphql_client = graphql_client
        self._session = session
        self._connector_id = connector_id

    async def fetch_discussions(
        self,
        repository: str,
        cursor: Optional[str] = None,
    ) -> tuple[list[GitHubDiscussion], list[GitHubComment], Optional[str], bool]:
        """Fetch discussions from repository.

        Args:
            repository: Repository full name (owner/repo).
            cursor: GraphQL pagination cursor.

        Returns:
            Tuple of (discussions, comments, new_cursor, has_more).
        """
        # Parse repository
        parts = repository.split("/", 1)
        if len(parts) != 2:
            logger.error(f"Invalid repository format: {repository}")
            return [], [], None, False

        owner, repo_name = parts

        try:
            data = await self._graphql_client.query_discussions(
                owner=owner,
                repo=repo_name,
                cursor=cursor,
            )

            repository_data = data.get("repository", {})
            discussions_data = repository_data.get("discussions", {})

            page_info = discussions_data.get("pageInfo", {})
            has_next_page = page_info.get("hasNextPage", False)
            end_cursor = page_info.get("endCursor")

            nodes = discussions_data.get("nodes", [])

            discussions: list[GitHubDiscussion] = []
            all_comments: list[GitHubComment] = []

            for node in nodes:
                discussion, comments = self._parse_discussion_node(node, repository)
                discussions.append(discussion)
                all_comments.extend(comments)

            return discussions, all_comments, end_cursor, has_next_page

        except GraphQLError as e:
            logger.error(f"GraphQL error fetching discussions: {e}")
            return [], [], None, False
        except Exception as e:
            logger.error(f"Error fetching discussions from {repository}: {e}")
            return [], [], None, False

    async def fetch_all_discussions(
        self,
        repository: str,
    ) -> tuple[list[GitHubDiscussion], list[GitHubComment]]:
        """Fetch all discussions with pagination.

        Args:
            repository: Repository full name (owner/repo).

        Returns:
            Tuple of (discussions, comments).
        """
        all_discussions: list[GitHubDiscussion] = []
        all_comments: list[GitHubComment] = []

        cursor = None
        has_more = True

        while has_more:
            discussions, comments, new_cursor, has_more = await self.fetch_discussions(
                repository=repository,
                cursor=cursor,
            )

            all_discussions.extend(discussions)
            all_comments.extend(comments)

            cursor = new_cursor

        return all_discussions, all_comments

    def _parse_discussion_node(
        self,
        node: dict,
        repository: str,
    ) -> tuple[GitHubDiscussion, list[GitHubComment]]:
        """Parse GraphQL discussion node.

        Args:
            node: Discussion node dict.
            repository: Repository full name.

        Returns:
            Tuple of (discussion, comments).
        """
        # Parse category
        category_data = node.get("category", {})
        category = GitHubDiscussionCategory(
            id=category_data.get("id", ""),
            name=category_data.get("name", ""),
            slug=category_data.get("slug", ""),
        )

        # Parse author
        author_data = node.get("author", {})
        author = GitHubUser(
            id=0,  # GraphQL doesn't provide ID in this query
            login=author_data.get("login", ""),
            avatar_url=author_data.get("avatarUrl"),
            type="User",
        )

        # Parse answer
        answer_data = node.get("answer")
        answer_id = answer_data.get("id") if answer_data else None

        # Parse timestamps
        created_at = self._parse_timestamp(node.get("createdAt"))
        updated_at = self._parse_timestamp(node.get("updatedAt"))

        discussion = GitHubDiscussion(
            id=node.get("id", ""),
            number=node.get("number", 0),
            title=node.get("title", ""),
            body=node.get("body"),
            category=category,
            answer_id=answer_id,
            upvote_count=node.get("upvoteCount", 0),
            comments_count=node.get("comments", {}).get("totalCount", 0),
            author=author,
            created_at=created_at,
            updated_at=updated_at,
            url=node.get("url", ""),
            repository=repository,
        )

        # Parse comments from discussion
        comments: list[GitHubComment] = []
        comments_data = node.get("comments", {})
        comment_nodes = comments_data.get("nodes", [])

        for comment_node in comment_nodes:
            comment_author_data = comment_node.get("author", {})
            comment = GitHubComment(
                id=int(comment_node.get("id", "").replace("DC_", ""), 16),
                body=comment_node.get("body", ""),
                user=GitHubUser(
                    id=0,
                    login=comment_author_data.get("login", ""),
                    avatar_url=comment_author_data.get("avatarUrl"),
                    type="User",
                ),
                created_at=self._parse_timestamp(comment_node.get("createdAt")),
                updated_at=self._parse_timestamp(comment_node.get("updatedAt")),
                discussion_number=discussion.number,
            )
            comments.append(comment)

        return discussion, comments

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
