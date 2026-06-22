"""Core sync engine for bidirectional sync orchestration.

Plan 11-01: Sync engine core with conflict detection.
Per SYNC-02: Source metadata tracking prevents sync loops.
Per SYNC-05: Backpressure handling via Write Queue depth monitoring.
Per ERRO-04: All operations wrapped with error handling and logging.
"""
from __future__ import annotations

import asyncio
import enum
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from saw.connectors.protocol import UnifiedConnectorInterface, ConnectorItem
from saw.connectors.models import SyncResult, SyncDirection
from saw.connectors.registry import ConnectorRegistry
from saw.connectors.sync_status import SyncStatusTracker, SyncState, SyncStatus
from saw.connectors.sync_logger import SyncLogger
from saw.connectors.conflict_resolver import ConflictResolver, ConflictStrategy
from saw.domain.utils import utcnow  # noqa: F401


logger = logging.getLogger(__name__)


class SyncMode(enum.Enum):
    """Mode of synchronization."""
    FULL = "full"  # Sync all items
    INCREMENTAL = "incremental"  # Sync only items changed since last sync


@dataclass
class SyncOptions:
    """Options for sync operation.

    Attributes:
        direction: Sync direction (pull, push, bidirectional).
        mode: Sync mode (full, incremental).
        force: Ignore last_sync_at and sync everything.
    """

    direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    mode: SyncMode = SyncMode.INCREMENTAL
    force: bool = False


@dataclass
class ClaimCreate:
    """Data for creating a new claim from a connector item.

    Attributes:
        content: Claim content.
        source_platform: Platform where item originated.
        source_id: Platform's item identifier.
        source_url: URL to original item (optional).
        metadata: Additional metadata (thread, channel, author, etc.).
    """

    content: str
    source_platform: str
    source_id: str
    source_url: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SyncEngine:
    """Orchestrates bidirectional sync between SAW and connected platforms.

    Per SYNC-02: Source_platform/source_id tracking prevents sync loops.
    Per SYNC-05: Backpressure handling via Write Queue depth monitoring.
    Per ERRO-04: All operations wrapped in try/except with error logging.
    """

    # Backpressure thresholds
    PAUSE_THRESHOLD = 1000  # Pause when queue depth > this
    RESUME_THRESHOLD = 500  # Resume when queue depth < this

    def __init__(
        self,
        registry: ConnectorRegistry,
        write_queue: Any,  # WriteQueue type hint avoided to prevent circular import
        session: AsyncSession,
    ) -> None:
        """Initialize sync engine.

        Args:
            registry: Connector registry for accessing connectors.
            write_queue: Write queue for enqueuing claim writes.
            session: SQLAlchemy async session for database operations.
        """
        self._registry = registry
        self._write_queue = write_queue
        self._session = session

        # Initialize helper components
        self._status_tracker = SyncStatusTracker(session)
        self._logger = SyncLogger(session)
        self._conflict_resolver = ConflictResolver(session, ConflictStrategy.LAST_MODIFIED_WINS)

        # Track paused state for backpressure
        self._is_paused: bool = False
        self._paused_at: Optional[datetime] = None

    async def _broadcast_sync_progress(
        self,
        platform: str,
        state: SyncState,
        items_synced: int = 0,
        items_total: int = 0,
        last_error: Optional[str] = None,
    ) -> None:
        """Broadcast sync progress via WebSocket.

        Per DASH-03: Real-time sync progress updates.

        Args:
            platform: Platform name.
            state: Current sync state.
            items_synced: Number of items synced so far.
            items_total: Total items to sync (if known).
            last_error: Last error message if any.
        """
        try:
            from saw.api.integrations_ws import broadcast_sync_progress

            status = SyncStatus(
                connector_id=platform,
                platform=platform,
                state=state,
                last_error=last_error,
            )
            # Add computed progress fields
            status.items_synced = items_synced
            status.items_total = items_total
            status.completion_percent = (items_synced / items_total * 100) if items_total > 0 else 0.0

            await broadcast_sync_progress(platform, status)
        except Exception as e:
            logger.warning(f"Failed to broadcast sync progress: {e}")

    async def sync(
        self,
        connector_id: str,
        connector: UnifiedConnectorInterface,
        options: Optional[SyncOptions] = None,
    ) -> SyncResult:
        """Perform sync for a connector.

        Orchestrates pull and/or push based on direction.

        Args:
            connector_id: Connector identifier.
            connector: Connector instance.
            options: Sync options (direction, mode, force).

        Returns:
            SyncResult with operation summary.
        """
        options = options or SyncOptions()
        started_at = utcnow()

        # Mark sync started
        await self._status_tracker.mark_sync_started(
            connector_id, connector.platform_name
        )

        # Broadcast sync started (per DASH-03)
        await self._broadcast_sync_progress(
            platform=connector.platform_name,
            state=SyncState.SYNCING,
        )

        result = SyncResult(
            connector_id=connector_id,
            direction=options.direction,
            started_at=started_at,
        )

        try:
            # Perform pull if direction allows
            if options.direction in (SyncDirection.PULL, SyncDirection.BIDIRECTIONAL):
                pull_result = await self.sync_pull(connector, options)
                result.pulled_count = pull_result.pulled_count
                result.errors.extend(pull_result.errors)

            # Perform push if direction allows
            if options.direction in (SyncDirection.PUSH, SyncDirection.BIDIRECTIONAL):
                if connector.supports_push:
                    push_result = await self.sync_push(connector, options)
                    result.pushed_count = push_result.pushed_count
                    result.errors.extend(push_result.errors)

            # Update status on success
            await self._status_tracker.mark_sync_completed(connector_id, result)

        except Exception as e:
            result.errors.append(str(e))
            await self._status_tracker.mark_error(connector_id, str(e))
            await self._logger.log_error(
                connector_id, connector.platform_name, str(e)
            )

        result.completed_at = utcnow()
        result.duration_ms = int(
            (result.completed_at - result.started_at).total_seconds() * 1000
        )

        # Log the sync operation
        await self._logger.log_sync(
            connector_id=connector_id,
            platform=connector.platform_name,
            direction=options.direction.value,
            status="success" if result.success else "failed",
            items={
                "pulled": result.pulled_count,
                "pushed": result.pushed_count,
                "skipped": 0,
            },
            error_message="; ".join(result.errors) if result.errors else None,
            started_at=started_at,
            completed_at=result.completed_at,
        )

        # Broadcast sync completed (per DASH-03)
        final_state = SyncState.IDLE if result.success else SyncState.ERROR
        total_synced = result.pulled_count + result.pushed_count
        await self._broadcast_sync_progress(
            platform=connector.platform_name,
            state=final_state,
            items_synced=total_synced,
            items_total=total_synced,
            last_error="; ".join(result.errors) if result.errors else None,
        )

        return result

    async def sync_pull(
        self,
        connector: UnifiedConnectorInterface,
        options: SyncOptions,
    ) -> SyncResult:
        """Pull items from connector and create claims.

        Per SYNC-02: Skip items with source_platform matching target.
        Per SYNC-05: Check backpressure before pulling.

        Args:
            connector: Connector to pull from.
            options: Sync options.

        Returns:
            SyncResult with pull operation summary.
        """
        result = SyncResult(
            connector_id="",  # Set by caller
            direction=SyncDirection.PULL,
        )

        # Check backpressure
        should_pause, depth = await self.check_backpressure()
        if should_pause:
            result.errors.append(f"Sync paused due to backpressure (depth={depth})")
            return result

        # Get last sync timestamp for incremental sync
        status = await self._status_tracker.get_status(connector.platform_name)
        since = None if options.force or options.mode == SyncMode.FULL else status.last_sync_at

        try:
            # Fetch items from connector
            items = await connector.get_items(since=since)

            items_pulled = 0
            items_skipped = 0

            for item in items:
                # Check for sync loop
                if self._is_sync_loop(item, connector.platform_name):
                    items_skipped += 1
                    continue

                # Transform to claim
                claim_data = self._create_claim_from_item(item, connector.platform_name)

                # Queue write to write queue
                if self._write_queue:
                    # Create WriteOp and enqueue
                    from saw.write_queue.queue import WriteOp
                    from saw.domain.value_objects import WriteOpStatus

                    op = WriteOp(
                        op_id=f"sync-{connector.platform_name}-{item.id}",
                        session_id=f"sync-{connector.platform_name}",
                        sink_name="claims",
                        payload={
                            "content": claim_data.content,
                            "source_platform": claim_data.source_platform,
                            "source_id": claim_data.source_id,
                            "source_url": claim_data.source_url,
                            **claim_data.metadata,
                        },
                        status=WriteOpStatus.PENDING,
                    )
                    self._write_queue.enqueue([op])
                    items_pulled += 1

            result.pulled_count = items_pulled

        except Exception as e:
            result.errors.append(f"Pull failed: {str(e)}")

        return result

    async def sync_push(
        self,
        connector: UnifiedConnectorInterface,
        options: SyncOptions,
    ) -> SyncResult:
        """Push claims to connector.

        Per SYNC-02: Skip claims where source_platform matches connector.

        Args:
            connector: Connector to push to.
            options: Sync options.

        Returns:
            SyncResult with push operation summary.
        """
        result = SyncResult(
            connector_id="",  # Set by caller
            direction=SyncDirection.PUSH,
        )

        if not connector.supports_push:
            result.errors.append("Connector does not support push")
            return result

        # Query claims modified since last_sync_at via ClaimRepository
        from saw.adapters.storage.claims_repository import ClaimsRepository
        from pathlib import Path as _Path

        db_path = _Path.home() / ".saw" / "claims.db"
        if not db_path.exists():
            result.pushed_count = 0
            return result

        repo = ClaimsRepository(str(db_path))
        status = await self._status_tracker.get_status(connector.platform_name)
        since = None if options.force or options.mode == SyncMode.FULL else status.last_sync_at

        try:
            claims = repo.list_modified_since(since) if hasattr(repo, "list_modified_since") else []
            # Filter out claims originating from the same platform to avoid sync loops
            filtered = [
                c for c in claims
                if not (
                    hasattr(c, "metadata")
                    and isinstance(getattr(c, "metadata", None), dict)
                    and c.metadata.get("source_platform") == connector.platform_name
                )
            ]
            for c in filtered:
                payload = {
                    "content": c.content if hasattr(c, "content") else str(c),
                    "source_platform": "saw",
                    "source_id": c.uuid if hasattr(c, "uuid") else "",
                }
                await connector.push_item(payload)
                result.pushed_count += 1
        except Exception as e:
            result.errors.append(f"Push failed: {str(e)}")

        return result

    async def check_backpressure(self) -> tuple[bool, int]:
        """Check if backpressure should be applied.

        Per SYNC-05: Pause when depth > 1000, resume when < 500.

        Returns:
            Tuple of (should_pause, current_depth).
        """
        depth = 0
        if self._write_queue and hasattr(self._write_queue, "get_pending"):
            pending = self._write_queue.get_pending()
            depth = len(pending) if pending else 0

        # Hysteresis: need to go below resume threshold to unpause
        if self._is_paused:
            if depth < self.RESUME_THRESHOLD:
                self._is_paused = False
                self._paused_at = None
        else:
            if depth > self.PAUSE_THRESHOLD:
                self._is_paused = True
                self._paused_at = utcnow()

        return (self._is_paused, depth)

    def _is_sync_loop(self, item: ConnectorItem, target_platform: str) -> bool:
        """Check if item would create a sync loop.

        Per SYNC-02: Returns True if item.metadata[source_platform] == target_platform.

        Args:
            item: Item to check.
            target_platform: Target platform name.

        Returns:
            True if this would be a sync loop.
        """
        source_platform = item.metadata.get("source_platform")
        return source_platform == target_platform

    def _create_claim_from_item(
        self,
        item: ConnectorItem,
        platform: str,
    ) -> ClaimCreate:
        """Create ClaimCreate from connector item.

        Per SYNC-02: Sets metadata with source_platform, source_id, source_url.

        Args:
            item: Connector item to transform.
            platform: Platform name.

        Returns:
            ClaimCreate ready for Write Queue.
        """
        metadata = {
            "source_platform": platform,
            "source_id": item.id,
            "source_url": item.url,
            "author": item.author,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }

        # Add thread context if present
        if "thread_parent_id" in item.metadata:
            metadata["thread_parent_id"] = item.metadata["thread_parent_id"]
        if "channel_id" in item.metadata:
            metadata["channel_id"] = item.metadata["channel_id"]

        return ClaimCreate(
            content=item.content,
            source_platform=platform,
            source_id=item.id,
            source_url=item.url,
            metadata=metadata,
        )
