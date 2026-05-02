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
from saw.connectors.github.oauth import GitHubOAuthHandler
from saw.connectors.github.app_installation import GitHubAppInstallationHandler
from saw.connectors.github.repository_selector import RepositorySelector
from saw.connectors.github.issue_fetcher import IssueFetcher
from saw.connectors.github.graphql_client import GitHubGraphQLClient, DiscussionFetcher
from saw.connectors.github.transformer import (
    GitHubTransformer,
    IssueTransformer,
    DiscussionTransformer,
)
from saw.connectors.github.webhook_handler import GitHubWebhookHandler
from saw.connectors.github.reconciliation import GitHubReconciler, ReconciliationScheduler

__all__ = [
    # Models
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
    # Connector
    "GitHubConnector",
    # Auth handlers
    "GitHubOAuthHandler",
    "GitHubAppInstallationHandler",
    # Repository management
    "RepositorySelector",
    # Fetchers
    "IssueFetcher",
    "GitHubGraphQLClient",
    "DiscussionFetcher",
    # Transformers
    "GitHubTransformer",
    "IssueTransformer",
    "DiscussionTransformer",
    # Webhook
    "GitHubWebhookHandler",
    # Reconciliation
    "GitHubReconciler",
    "ReconciliationScheduler",
]
