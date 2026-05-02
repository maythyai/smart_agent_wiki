"""GitHub connector package.

Plan 14-01: GitHub connector core with OAuth/App auth.
Plan 14-02: Issue/Discussion ingestion with GraphQL.
Plan 14-03: Webhooks and reconciliation.
"""

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
from saw.connectors.github.connector import GitHubConnector

__all__ = [
    "GitHubUser",
    "GitHubLabel",
    "GitHubMilestone",
    "GitHubIssue",
    "GitHubComment",
    "GitHubDiscussion",
    "GitHubDiscussionCategory",
    "GitHubRepository",
    "GitHubRateLimit",
    "GitHubSearchResult",
    "GitHubWebhookEvent",
    "GitHubAuthType",
    "GitHubAppInstallation",
    "GitHubConnector",
]
