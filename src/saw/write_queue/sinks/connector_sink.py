"""Write Queue sink for connector sync operations.

Plan 11-03: IM message handling and sync API endpoints.
Per SYNC-05: Write Queue integration for backpressure.
Per IM-07: Graceful degradation when platforms unavailable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from saw.connectors.sync_engine import SyncEngine, SyncOptions, SyncMode
from saw.connectors.backpressure import BackpressureManager
from saw.connectors.retry_handler import RetryHandler, RetryConfig, TransientError
from saw.connectors.health_monitor import HealthMonitor
from saw.connectors.sync_logger import SyncLogger
from saw.connectors.registry import ConnectorRegistry
from saw.connectors.protocol import SyncDirection
from saw.write_queue.queue import WriteOp


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


@dataclass
class ConnectorSinkConfig:
    """Configuration for connector sink.

    Attributes:
        enabled_connectors: Which connectors to push to.
        batch_size: Items per push batch.
        batch_timeout_seconds: Max wait before flush.
        retry_config: Retry configuration for failed pushes.
    """

    enabled_connectors: list[str] = field(default_factory=list)
    batch_size: int = 10
    batch_timeout_seconds: float = 5.0
    retry_config: Optional[RetryConfig] = None


@dataclass
class SinkResult:
    """Result of sink processing.

    Attributes:
        success: Whether processing succeeded.
        connector_id: Connector that processed item.
        items_pushed: Number of items pushed.
        error: Error message if failed.
    """

    success: bool
    connector_id: Optional[str] = None
    items_pushed: int = 0
    error: Optional[str] = None


class ConnectorSink:
    """Write Queue sink for connector sync operations.

    Per SYNC-05: Write Queue integration for backpressure.
    Per IM-07: Graceful degradation when platforms unavailable.

    This sink processes Claim writes from the Write Queue and
    pushes them to enabled connectors.
    """

    def __init__(
        self,
        config: ConnectorSinkConfig,
        sync_engine: SyncEngine,
        registry: ConnectorRegistry,
        session: Any,
    ) -> None:
        """Initialize connector sink.

        Args:
            config: Sink configuration.
            sync_engine: SyncEngine for push operations.
            registry: Connector registry.
            session: Database session.
        """
        self._config = config
        self._sync_engine = sync_engine
        self._registry = registry
        self._session = session

        # Helper components
        self._retry_handler = RetryHandler(config.retry_config)
        self._logger = SyncLogger(session)
        self._health_monitor = HealthMonitor(session)

    async def process(self, item: WriteOp) -> SinkResult:
        """Process a single write operation.

        Args:
            item: QueuedWrite to process.

        Returns:
            SinkResult indicating success or failure.
        """
        if not self.should_process(item):
            return SinkResult(success=True, items_pushed=0)

        payload = item.payload
        source_platform = payload.get("source_platform")

        results = []
        errors = []

        for connector_name in self._config.enabled_connectors:
            # Skip if source_platform matches (loop prevention)
            if source_platform == connector_name:
                continue

            connector = self._registry.get(connector_name)
            if connector is None:
                continue

            if not connector.supports_push:
                continue

            # Check health before pushing
            health = await self._health_monitor.get_health(connector_name)
            if health.status.value == "unhealthy":
                errors.append(f"Connector {connector_name} is unhealthy")
                continue

            # Push to connector with retry
            try:
                result = await self._retry_handler.execute(
                    self._push_to_connector,
                    connector_name,
                    payload,
                )

                if result.success:
                    results.append(connector_name)
                    await self._health_monitor.record_success(
                        connector_name, connector.platform_name
                    )
                else:
                    errors.append(f"{connector_name}: {result.last_error}")
                    await self._health_monitor.record_failure(
                        connector_name, connector.platform_name,
                        str(result.last_error),
                    )

            except Exception as e:
                errors.append(f"{connector_name}: {str(e)}")

        return SinkResult(
            success=len(errors) == 0,
            items_pushed=len(results),
            error="; ".join(errors) if errors else None,
        )

    async def process_batch(self, items: list[WriteOp]) -> list[SinkResult]:
        """Process multiple items in batch.

        Groups items by target connector for efficiency.

        Args:
            items: List of QueuedWrite items.

        Returns:
            List of SinkResult for each item.
        """
        results = []

        # Group by connector for batched push
        connector_items: dict[str, list[WriteOp]] = {}
        for item in items:
            if self.should_process(item):
                source_platform = item.payload.get("source_platform")
                for connector_name in self._config.enabled_connectors:
                    if source_platform != connector_name:
                        if connector_name not in connector_items:
                            connector_items[connector_name] = []
                        connector_items[connector_name].append(item)

        # Process each connector's batch
        for connector_name, batch in connector_items.items():
            # Process items for this connector
            for item in batch:
                result = await self.process(item)
                results.append(result)

        return results

    async def is_healthy(self) -> bool:
        """Check if sink is healthy.

        Returns:
            True if all enabled connectors are healthy.
        """
        for connector_name in self._config.enabled_connectors:
            health = await self._health_monitor.get_health(connector_name)
            if health.status.value == "unhealthy":
                return False

        return True

    def should_process(self, item: WriteOp) -> bool:
        """Check if item should be processed.

        Args:
            item: QueuedWrite to check.

        Returns:
            True if item should be pushed to connectors.
        """
        # Only process claim writes
        if item.sink_name != "claims":
            return False

        payload = item.payload
        source_platform = payload.get("source_platform")

        # Skip if no enabled connectors
        if not self._config.enabled_connectors:
            return False

        # Check if any connector would accept this
        for connector_name in self._config.enabled_connectors:
            if source_platform != connector_name:
                connector = self._registry.get(connector_name)
                if connector and connector.supports_push:
                    return True

        return False

    async def _push_to_connector(
        self,
        connector_name: str,
        payload: dict,
    ) -> None:
        """Push item to connector.

        Args:
            connector_name: Target connector.
            payload: Claim data to push.

        Raises:
            TransientError: If push fails temporarily.
        """
        connector = self._registry.get(connector_name)
        if connector is None:
            raise TransientError(f"Connector {connector_name} not available")

        # Transform payload to ConnectorItem
        from saw.connectors.protocol import ConnectorItem

        item = ConnectorItem(
            id=payload.get("source_id", ""),
            title=payload.get("title", ""),
            content=payload.get("content", ""),
            url=payload.get("source_url"),
            author=payload.get("author_name"),
            created_at=utcnow(),
            updated_at=utcnow(),
            metadata=payload,
        )

        # Push to connector
        result = await connector.put_item(item)

        if not result:
            raise TransientError(f"Push to {connector_name} failed")

    @property
    def name(self) -> str:
        """Sink name for registration."""
        return "connector"

    def can_handle(self, sink_name: str) -> bool:
        """Check if this sink can handle the given sink name."""
        return sink_name == "connector" or (
            sink_name == "claims" and len(self._config.enabled_connectors) > 0
        )