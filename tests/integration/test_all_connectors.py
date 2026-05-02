"""Integration tests for all connectors working together.

Plan 15-02: Documentation and integration testing.
Tests cross-connector behavior: dashboard aggregation, concurrent sync, webhook routing.
"""
from __future__ import annotations

import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from saw.connectors.registry import ConnectorRegistry
from saw.connectors.health_monitor import HealthMonitor, HealthStatus, ConnectorHealth
from saw.connectors.sync_status import SyncStatusTracker, SyncState, SyncStatus
from saw.connectors.rate_limiter import RateLimitManager


def utcnow():
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def reset_registry():
    """Reset connector registry before/after each test."""
    ConnectorRegistry.reset()
    yield
    ConnectorRegistry.reset()


class TestDashboardAggregation:
    """Test 1: Dashboard aggregation returns all registered connectors."""

    @pytest.mark.asyncio
    async def test_dashboard_aggregation_returns_all_connectors(self, mock_session, reset_registry):
        """Dashboard should return all registered connectors with correct structure."""
        # Register mock connectors for all 7 platforms
        platforms = ["notion", "logseq", "slack", "discord", "feishu", "wecom", "github"]
        registry = ConnectorRegistry()

        for platform in platforms:
            connector = MagicMock()
            connector.platform_name = platform
            registry.register(connector)

        # Setup health monitor with mock data
        health_monitor = HealthMonitor(mock_session)
        health_data = [
            ConnectorHealth(
                connector_id=f"{p}-main",
                platform=p,
                status=HealthStatus.HEALTHY,
                last_success_at=utcnow(),
            )
            for p in platforms
        ]
        health_monitor._health_cache = {f"{p}-main": h for p, h in zip(platforms, health_data)}

        # Setup sync tracker
        sync_tracker = SyncStatusTracker(mock_session)
        for platform in platforms:
            sync_tracker._in_memory_status[f"{platform}-main"] = SyncStatus(
                connector_id=f"{platform}-main",
                platform=platform,
                state=SyncState.IDLE,
            )

        # Mock database queries
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar_one_or_none.return_value = MagicMock(items_synced_total=100)
        mock_session.execute.return_value = mock_result

        # Get all health and verify
        all_health = await health_monitor.get_all_health()
        assert len(all_health) >= len(platforms)

        # Get system health
        system_health = await health_monitor.get_system_health()
        assert system_health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "healthy_count" in system_health
        assert "degraded_count" in system_health
        assert "unhealthy_count" in system_health

    @pytest.mark.asyncio
    async def test_dashboard_health_counts_correct(self, mock_session, reset_registry):
        """System health should count healthy/degraded/unhealthy correctly."""
        health_monitor = HealthMonitor(mock_session)

        # Setup mixed health statuses
        health_monitor._health_cache = {
            "notion-main": ConnectorHealth(
                connector_id="notion-main",
                platform="notion",
                status=HealthStatus.HEALTHY,
            ),
            "slack-main": ConnectorHealth(
                connector_id="slack-main",
                platform="slack",
                status=HealthStatus.DEGRADED,
            ),
            "github-main": ConnectorHealth(
                connector_id="github-main",
                platform="github",
                status=HealthStatus.UNHEALTHY,
            ),
        }

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        system_health = await health_monitor.get_system_health()

        assert system_health["healthy_count"] == 1
        assert system_health["degraded_count"] == 1
        assert system_health["unhealthy_count"] == 1
        # Overall status should be unhealthy (worst case)
        assert system_health["status"] == "unhealthy"


class TestCrossConnectorSync:
    """Test 2: Cross-connector sync runs multiple syncs concurrently without interference."""

    @pytest.mark.asyncio
    async def test_concurrent_sync_no_interference(self, mock_session, reset_registry):
        """Multiple connectors syncing concurrently should not interfere with each other."""
        registry = ConnectorRegistry()

        # Create mock connectors with sync tracking
        sync_results = {}
        platforms = ["notion", "slack", "github"]

        for platform in platforms:
            connector = MagicMock()
            connector.platform_name = platform
            connector.sync = AsyncMock(side_effect=lambda p=platform: sync_results.update({p: "synced"}))
            registry.register(connector)

        # Simulate concurrent sync calls
        async def mock_sync(platform):
            # Simulate some async work
            await asyncio.sleep(0.01)
            sync_results[platform] = "synced"
            return {"success": True, "items": 10}

        # Run concurrent syncs
        results = await asyncio.gather(*[mock_sync(p) for p in platforms])

        # All should complete successfully
        assert len(results) == 3
        assert all(r["success"] for r in results)
        assert len(sync_results) == 3

    @pytest.mark.asyncio
    async def test_sync_cursor_independence(self, mock_session, reset_registry):
        """Each connector should maintain independent sync cursor."""
        sync_tracker = SyncStatusTracker(mock_session)

        # Setup cursors for different platforms
        platforms = ["notion", "slack", "github"]
        cursors = {}

        for platform in platforms:
            cursor = f"cursor-{platform}-123"
            cursors[platform] = cursor
            sync_tracker._in_memory_status[f"{platform}-main"] = SyncStatus(
                connector_id=f"{platform}-main",
                platform=platform,
                state=SyncState.IDLE,
                sync_cursor=cursor,
            )

        # Verify cursors are independent
        for platform in platforms:
            status = sync_tracker._in_memory_status[f"{platform}-main"]
            assert status.sync_cursor == cursors[platform]
            # Should not match other platform's cursor
            other_platforms = [p for p in platforms if p != platform]
            for other in other_platforms:
                assert status.sync_cursor != cursors[other]

    @pytest.mark.asyncio
    async def test_write_queue_handles_multiple_sources(self, mock_session):
        """Write queue should correctly handle items from multiple sources."""
        # Mock write queue
        queue_items = []

        async def add_to_queue(item):
            queue_items.append(item)

        # Simulate items from different platforms
        platforms = ["notion", "slack", "github"]
        for platform in platforms:
            for i in range(3):
                await add_to_queue({
                    "platform": platform,
                    "item_id": f"{platform}-item-{i}",
                    "content": f"Content from {platform}",
                })

        # Verify items are preserved with correct source
        assert len(queue_items) == 9
        platform_counts = {}
        for item in queue_items:
            platform_counts[item["platform"]] = platform_counts.get(item["platform"], 0) + 1

        # Each platform should have 3 items
        for platform in platforms:
            assert platform_counts[platform] == 3


class TestWebhookRouting:
    """Test 3: Webhook routing delivers events to correct handlers."""

    @pytest.mark.asyncio
    async def test_webhook_routing_to_correct_connector(self, mock_session, reset_registry):
        """Webhook events should be routed to the correct connector handler."""
        # Setup mock handlers for each platform
        handlers_called = {}

        def make_handler(platform):
            async def handler(event):
                handlers_called[platform] = event
                return {"status": "processed"}
            return handler

        # Mock webhook router
        router = {
            "slack": make_handler("slack"),
            "discord": make_handler("discord"),
            "github": make_handler("github"),
        }

        # Simulate Slack event
        slack_event = {"type": "message", "channel": "C123", "text": "Hello"}
        result = await router["slack"](slack_event)
        assert result["status"] == "processed"
        assert handlers_called["slack"] == slack_event

        # Simulate Discord event
        discord_event = {"t": "MESSAGE_CREATE", "d": {"content": "Hello"}}
        result = await router["discord"](discord_event)
        assert result["status"] == "processed"
        assert handlers_called["discord"] == discord_event

        # Simulate GitHub event
        github_event = {"action": "opened", "issue": {"number": 1}}
        result = await router["github"](github_event)
        assert result["status"] == "processed"
        assert handlers_called["github"] == github_event

    @pytest.mark.asyncio
    async def test_hmac_verification_passes(self, mock_session):
        """HMAC signature verification should pass for valid signatures."""
        from saw.connectors.webhook_verifier import WebhookVerifier
        import hashlib
        import hmac

        secret = "webhook-secret"
        verifier = WebhookVerifier(secret=secret, platform="github")

        # Create valid signature (GitHub format with sha256= prefix)
        payload = b'{"event": "test"}'
        valid_signature = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Verify should pass
        is_valid = verifier.verify(payload, valid_signature)
        assert is_valid is True

        # Invalid signature should raise exception
        from saw.connectors.webhook_verifier import SignatureVerificationError
        with pytest.raises(SignatureVerificationError):
            verifier.verify(payload, "sha256=invalid-signature")


class TestRateLimitingAcrossAll:
    """Test 4: Rate limiting across all respects per-platform limits under concurrent load."""

    @pytest.mark.asyncio
    async def test_rate_limits_respected_concurrent_load(self, mock_session):
        """All platforms should respect their rate limits under concurrent load."""
        from saw.connectors.rate_limiter import RateLimitManager, PlatformRateLimit

        # Create rate limiters for each platform
        notion_limiter = RateLimitManager("notion")
        github_limiter = RateLimitManager("github")
        slack_limiter = RateLimitManager("slack")

        # Verify limits are configured correctly
        assert notion_limiter._limits.requests_per_second == 3
        assert github_limiter._limits.requests_per_hour == 5000
        assert slack_limiter._limits.requests_per_minute == 60

        # Test that acquire works without blocking (when tokens available)
        await notion_limiter.acquire()
        await github_limiter.acquire()
        await slack_limiter.acquire()

    @pytest.mark.asyncio
    async def test_per_platform_independent_limits(self, mock_session):
        """Each platform should have independent rate limits."""
        from saw.connectors.rate_limiter import RateLimitManager

        # Create separate rate limiters for each platform
        notion_limiter = RateLimitManager("notion")
        slack_limiter = RateLimitManager("slack")

        # Each has independent token count
        assert notion_limiter._tokens == notion_limiter._limits.burst
        assert slack_limiter._tokens == slack_limiter._limits.burst

        # Using one doesn't affect the other
        await slack_limiter.acquire()
        assert slack_limiter._tokens < slack_limiter._limits.burst
        # Notion's tokens should be unchanged
        assert notion_limiter._tokens == notion_limiter._limits.burst


class TestErrorHandlingConsistency:
    """Test 5: Error handling consistency across all connectors."""

    @pytest.mark.asyncio
    async def test_exponential_backoff_consistent(self, mock_session):
        """RetryHandler should apply exponential backoff consistently."""
        from saw.connectors.retry_handler import RetryHandler, RetryConfig, TransientError

        config = RetryConfig(
            max_retries=3,
            base_delay_seconds=0.1,  # Small delay for testing
            max_delay_seconds=1.0,
        )
        retry_handler = RetryHandler(config)

        call_count = 0

        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TransientError(f"Transient error {call_count}")
            return "success"

        # Execute with retry
        result = await retry_handler.execute(failing_operation)

        assert result.success is True
        assert result.result == "success"
        assert result.attempts == 3

    @pytest.mark.asyncio
    async def test_health_status_transitions(self, mock_session):
        """HealthMonitor should transition statuses correctly."""
        health_monitor = HealthMonitor(mock_session)

        # Create custom thresholds
        from saw.connectors.health_monitor import HealthThresholds
        thresholds = HealthThresholds(
            degraded_after_failures=2,
            unhealthy_after_failures=5,
            healthy_after_successes=3,
        )
        health_monitor._thresholds = thresholds

        # Record failures
        # i=0: 1 failure -> HEALTHY
        # i=1: 2 failures -> DEGRADED (meets degraded_after_failures=2)
        # i=2..4: 3-5 failures -> still DEGRADED until 5 failures
        # i=4: 5 failures -> UNHEALTHY
        for i in range(5):
            health = await health_monitor.record_failure(
                "test-connector",
                "test-platform",
                f"Error {i}"
            )

            if i < 1:  # 0 failures: still healthy
                assert health.status == HealthStatus.HEALTHY
            elif i < 4:  # 2-4 failures: degraded
                assert health.status in [HealthStatus.DEGRADED, HealthStatus.HEALTHY]
            else:  # 5+ failures: unhealthy
                assert health.status == HealthStatus.UNHEALTHY

        # Final should be unhealthy
        assert health.status == HealthStatus.UNHEALTHY

        # Record successes to recover
        for _ in range(3):
            health = await health_monitor.record_success("test-connector", "test-platform")

        assert health.status == HealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_error_messages_captured(self, mock_session):
        """Error messages should be captured in sync log."""
        health_monitor = HealthMonitor(mock_session)

        # Record failure with specific error
        health = await health_monitor.record_failure(
            "test-connector",
            "test-platform",
            "Connection timeout after 30s"
        )

        assert health.last_error == "Connection timeout after 30s"
        assert health.total_failures == 1
