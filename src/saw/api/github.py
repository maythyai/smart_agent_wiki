"""FastAPI endpoints for GitHub connector.

Plan 14-01: GitHub connector core with OAuth/App auth.
Per GITH-02: Repository selection API endpoints.
Per GITH-09: Rate limit status endpoint.
"""
from __future__ import annotations

from typing import Annotated, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from saw.db.session import get_db_session as get_session
from saw.connectors.github.connector import GitHubConnector
from saw.connectors.github.repository_selector import RepositorySelector
from saw.connectors.github.models import GitHubRateLimit
from saw.connectors.registry import ConnectorRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/connectors/github", tags=["github"])


class RepositorySelectRequest(BaseModel):
    """Request body for repository selection."""
    repository_ids: list[str]


class RepositorySyncSettings(BaseModel):
    """Request body for sync settings update."""
    sync_issues: Optional[bool] = None
    sync_discussions: Optional[bool] = None
    sync_comments: Optional[bool] = None
    label_tag_mapping: Optional[dict[str, str]] = None


class RepositoryResponse(BaseModel):
    """Response for repository listing."""
    repositories: list[dict]


class RepositorySelectionResponse(BaseModel):
    """Response for repository selection."""
    selected: int
    total_accessible: int


class RateLimitResponse(BaseModel):
    """Response for rate limit status."""
    limit: int
    remaining: int
    reset: str
    used: int


class SyncStatusResponse(BaseModel):
    """Response for sync status."""
    platform: str
    repositories: list[dict]
    rate_limit: dict


async def get_github_connector(
    session: AsyncSession = Depends(get_session)
) -> GitHubConnector:
    """Dependency to get GitHub connector instance.

    Args:
        session: SQLAlchemy async session.

    Returns:
        GitHubConnector instance.

    Raises:
        HTTPException: If connector not found.
    """
    registry = ConnectorRegistry()
    connector = registry.get("github")
    if not connector:
        raise HTTPException(404, "GitHub connector not registered")
    if not isinstance(connector, GitHubConnector):
        raise HTTPException(500, "Invalid connector type")
    return connector


@router.get("/repositories", response_model=RepositoryResponse)
async def list_repositories(
    connector: GitHubConnector = Depends(get_github_connector),
    session: AsyncSession = Depends(get_session),
) -> RepositoryResponse:
    """List accessible GitHub repositories.

    Returns repositories where user has write access
    and issues or discussions are enabled.

    Returns:
        RepositoryResponse with list of repositories.
    """
    repositories = await connector.list_repositories()

    return RepositoryResponse(
        repositories=[
            {
                "id": repo.full_name,
                "full_name": repo.full_name,
                "description": repo.description,
                "has_issues": repo.has_issues,
                "has_discussions": repo.has_discussions,
                "is_private": repo.is_private,
                "html_url": repo.html_url,
            }
            for repo in repositories
        ]
    )


@router.post("/repositories/select", response_model=RepositorySelectionResponse)
async def select_repositories(
    request: RepositorySelectRequest,
    connector: GitHubConnector = Depends(get_github_connector),
    session: AsyncSession = Depends(get_session),
) -> RepositorySelectionResponse:
    """Select repositories for sync.

    Persists repository selection to database.
    Clears previous selections.

    Args:
        request: Repository selection request with repository_ids.

    Returns:
        RepositorySelectionResponse with counts.
    """
    selector = RepositorySelector(
        connector=connector,
        session=session,
        connector_id=connector._config.id,
    )

    selected, total = await selector.select_repositories(request.repository_ids)
    await session.commit()

    return RepositorySelectionResponse(
        selected=selected,
        total_accessible=total,
    )


@router.get("/repositories/selected")
async def get_selected_repositories(
    connector: GitHubConnector = Depends(get_github_connector),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get currently selected repositories with sync settings.

    Returns:
        Dict with list of selected repositories and their settings.
    """
    selector = RepositorySelector(
        connector=connector,
        session=session,
        connector_id=connector._config.id,
    )

    repositories = await selector.get_selected_repositories()

    return {
        "repositories": [
            {
                "repository_id": repo.repository_id,
                "repository_name": repo.repository_name,
                "sync_issues": repo.sync_issues,
                "sync_discussions": repo.sync_discussions,
                "sync_comments": repo.sync_comments,
                "label_tag_mapping": repo.label_tag_mapping,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
            }
            for repo in repositories
        ]
    }


@router.patch("/repositories/{repository_id:path}")
async def update_repository_settings(
    repository_id: str,
    settings: RepositorySyncSettings,
    connector: GitHubConnector = Depends(get_github_connector),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Update sync settings for a repository.

    Args:
        repository_id: Repository full name (owner/repo).
        settings: New sync settings.

    Returns:
        Dict with update status.
    """
    selector = RepositorySelector(
        connector=connector,
        session=session,
        connector_id=connector._config.id,
    )

    update_data = settings.model_dump(exclude_unset=True)
    success = await selector.update_sync_settings(repository_id, update_data)

    if not success:
        raise HTTPException(404, f"Repository {repository_id} not found")

    await session.commit()

    return {"status": "updated", "repository_id": repository_id}


@router.delete("/repositories/{repository_id:path}")
async def deselect_repository(
    repository_id: str,
    connector: GitHubConnector = Depends(get_github_connector),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Deselect a repository from sync.

    Args:
        repository_id: Repository full name (owner/repo).

    Returns:
        Dict with deselection status.
    """
    selector = RepositorySelector(
        connector=connector,
        session=session,
        connector_id=connector._config.id,
    )

    success = await selector.deselect_repository(repository_id)

    if not success:
        raise HTTPException(404, f"Repository {repository_id} not found")

    await session.commit()

    return {"status": "deselected", "repository_id": repository_id}


@router.get("/rate-limit", response_model=RateLimitResponse)
async def get_rate_limit(
    connector: GitHubConnector = Depends(get_github_connector),
) -> RateLimitResponse:
    """Get current GitHub API rate limit status.

    Returns:
        RateLimitResponse with rate limit details.
    """
    rate_limit = await connector.check_rate_limit()

    return RateLimitResponse(
        limit=rate_limit.limit,
        remaining=rate_limit.remaining,
        reset=rate_limit.reset.isoformat(),
        used=rate_limit.used,
    )


@router.get("/status")
async def get_sync_status(
    connector: GitHubConnector = Depends(get_github_connector),
    session: AsyncSession = Depends(get_session),
) -> SyncStatusResponse:
    """Get overall sync status for GitHub connector.

    Returns:
        SyncStatusResponse with repositories and rate limit info.
    """
    selector = RepositorySelector(
        connector=connector,
        session=session,
        connector_id=connector._config.id,
    )

    repositories = await selector.get_selected_repositories()
    rate_limit = await connector.check_rate_limit()

    return SyncStatusResponse(
        platform="github",
        repositories=[
            {
                "repository_id": repo.repository_id,
                "sync_issues": repo.sync_issues,
                "sync_discussions": repo.sync_discussions,
            }
            for repo in repositories
        ],
        rate_limit={
            "remaining": rate_limit.remaining,
            "limit": rate_limit.limit,
            "reset": rate_limit.reset.isoformat(),
        },
    )


@router.get("/health")
async def health_check() -> dict:
    """Health check for GitHub webhook endpoint.

    Returns:
        Dict with status.
    """
    return {"status": "ok"}
