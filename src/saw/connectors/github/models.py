"""GitHub API models using Pydantic.

Plan 14-01: GitHub connector core with OAuth/App auth.
Per GITH-01: GitHub API models for Issues, Discussions, Repositories.
"""
from __future__ import annotations

from dataclasses import field
from datetime import datetime
from typing import Any, Literal, Optional
import enum

from pydantic import BaseModel, ConfigDict


class GitHubUser(BaseModel):
    """GitHub user (person or bot).

    Attributes:
        id: User identifier.
        login: Username.
        avatar_url: Avatar URL.
        type: User type (User or Bot).
        html_url: Profile URL.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    login: str
    avatar_url: Optional[str] = None
    type: Literal["User", "Bot", "Organization"] = "User"
    html_url: Optional[str] = None


class GitHubLabel(BaseModel):
    """GitHub issue label.

    Attributes:
        id: Label identifier.
        name: Label name.
        color: Label color (hex).
        description: Label description.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str = "default"
    description: Optional[str] = None


class GitHubMilestone(BaseModel):
    """GitHub milestone.

    Attributes:
        id: Milestone identifier.
        number: Milestone number.
        title: Milestone title.
        state: Milestone state (open/closed).
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    title: str
    state: Literal["open", "closed"] = "open"


class GitHubIssue(BaseModel):
    """GitHub issue.

    Attributes:
        id: Issue identifier.
        number: Issue number in repository.
        title: Issue title.
        body: Issue body content.
        state: Issue state (open/closed).
        labels: List of labels.
        assignees: List of assignees.
        milestone: Milestone (optional).
        comments_count: Number of comments.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        closed_at: Closure timestamp (optional).
        user: Issue author.
        url: API URL.
        html_url: Web URL.
        repository: Repository full name (owner/repo).
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    number: int
    title: str
    body: Optional[str] = None
    state: Literal["open", "closed"] = "open"
    labels: list[GitHubLabel] = field(default_factory=list)
    assignees: list[GitHubUser] = field(default_factory=list)
    milestone: Optional[GitHubMilestone] = None
    comments_count: int = 0
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    user: GitHubUser
    url: str
    html_url: str
    repository: str  # owner/name format


class GitHubComment(BaseModel):
    """GitHub comment on issue or discussion.

    Attributes:
        id: Comment identifier.
        body: Comment body.
        user: Comment author.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        issue_number: Issue number (for issue comments).
        discussion_number: Discussion number (for discussion comments).
        html_url: Web URL.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str
    user: GitHubUser
    created_at: datetime
    updated_at: datetime
    issue_number: Optional[int] = None
    discussion_number: Optional[int] = None
    html_url: Optional[str] = None


class GitHubDiscussionCategory(BaseModel):
    """GitHub discussion category.

    Attributes:
        id: Category identifier.
        name: Category name.
        slug: Category slug.
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str


class GitHubDiscussion(BaseModel):
    """GitHub discussion.

    Attributes:
        id: Discussion identifier (GraphQL ID).
        number: Discussion number in repository.
        title: Discussion title.
        body: Discussion body content.
        category: Discussion category.
        answer_id: Answer comment ID (optional).
        upvote_count: Number of upvotes.
        comments_count: Number of comments.
        author: Discussion author.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        url: Discussion URL.
        repository: Repository full name (owner/repo).
    """
    model_config = ConfigDict(from_attributes=True)

    id: str
    number: int
    title: str
    body: Optional[str] = None
    category: GitHubDiscussionCategory
    answer_id: Optional[str] = None
    upvote_count: int = 0
    comments_count: int = 0
    author: GitHubUser
    created_at: datetime
    updated_at: datetime
    url: str
    repository: str  # owner/name format


class GitHubRepository(BaseModel):
    """GitHub repository.

    Attributes:
        id: Repository identifier.
        owner: Repository owner (login).
        name: Repository name.
        full_name: Full name (owner/name).
        description: Repository description.
        topics: List of topics.
        has_issues: Whether issues are enabled.
        has_discussions: Whether discussions are enabled.
        permissions: User permissions dict.
        html_url: Web URL.
        is_private: Whether repository is private.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner: str
    name: str
    full_name: str
    description: Optional[str] = None
    topics: list[str] = field(default_factory=list)
    has_issues: bool = True
    has_discussions: bool = False
    permissions: dict[str, bool] = field(default_factory=dict)
    html_url: str
    is_private: bool = False


class GitHubRateLimit(BaseModel):
    """GitHub rate limit status.

    Attributes:
        limit: Maximum requests per hour.
        remaining: Remaining requests.
        reset: Reset timestamp.
        used: Used requests.
    """
    model_config = ConfigDict(from_attributes=True)

    limit: int = 5000
    remaining: int = 5000
    reset: datetime
    used: int = 0


class GitHubSearchResult(BaseModel):
    """GitHub search result.

    Attributes:
        total_count: Total matching items.
        incomplete_results: Whether results are incomplete.
        items: List of matching items.
    """
    model_config = ConfigDict(from_attributes=True)

    total_count: int = 0
    incomplete_results: bool = False
    items: list[Any] = field(default_factory=list)


class GitHubWebhookEvent(BaseModel):
    """GitHub webhook event payload.

    Attributes:
        delivery_id: Unique delivery ID (X-GitHub-Delivery).
        event_type: Event type (X-GitHub-Event).
        action: Event action (opened, closed, etc.).
        payload: Raw event payload.
        repository: Repository full name.
        sender: Event sender login.
        received_at: Reception timestamp.
    """
    model_config = ConfigDict(from_attributes=True)

    delivery_id: str
    event_type: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    repository: str
    sender: str
    received_at: datetime = field(default_factory=lambda: datetime.now(datetime.now().astimezone().tzinfo))


class GitHubAuthType(enum.Enum):
    """GitHub authentication type."""
    OAUTH = "oauth"
    APP_INSTALLATION = "app_installation"


class GitHubAppInstallation(BaseModel):
    """GitHub App installation info.

    Attributes:
        id: Installation ID.
        account: Account (user or org) that installed the app.
        repository_selection: selected or all.
        permissions: Granted permissions.
        events: Subscribed events.
        created_at: Installation timestamp.
        updated_at: Last update timestamp.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    account: GitHubUser
    repository_selection: Literal["selected", "all"] = "all"
    permissions: dict[str, str] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    created_at: datetime
    updated_at: datetime
