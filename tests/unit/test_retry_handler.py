"""Tests for retry handler with exponential backoff.

Plan 11-02, Task 2: RetryHandler.
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from saw.connectors.retry_handler import (
    RetryConfig,
    RetryResult,
    TransientError,
    PermanentError,
    ErrorCategory,
    RetryHandler,
    with_retry,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = RetryConfig()
        assert config.max_retries == 5
        assert config.base_delay_seconds == 1.0
        assert config.max_delay_seconds == 16.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_config_custom(self):
        """Test custom configuration values."""
        config = RetryConfig(
            max_retries=3,
            base_delay_seconds=0.5,
            max_delay_seconds=8.0,
            jitter=False,
        )
        assert config.max_retries == 3
        assert config.base_delay_seconds == 0.5


class TestTransientError:
    """Tests for TransientError."""

    def test_transient_error_creation(self):
        """Test creating TransientError."""
        error = TransientError("Rate limit exceeded", retry_after=60.0)
        assert str(error) == "Rate limit exceeded"
        assert error.retry_after == 60.0

    def test_transient_error_no_retry_after(self):
        """Test TransientError without retry_after."""
        error = TransientError("Connection timeout")
        assert error.retry_after is None


class TestPermanentError:
    """Tests for PermanentError."""

    def test_permanent_error_creation(self):
        """Test creating PermanentError."""
        error = PermanentError("Unauthorized")
        assert str(error) == "Unauthorized"


class TestRetryResult:
    """Tests for RetryResult."""

    def test_result_creation(self):
        """Test creating RetryResult."""
        result = RetryResult(
            success=True,
            result="value",
            attempts=3,
        )
        assert result.success is True
        assert result.result == "value"
        assert result.attempts == 3

    def test_result_failure(self):
        """Test RetryResult for failure."""
        error = ValueError("test")
        result = RetryResult(
            success=False,
            last_error=error,
            attempts=5,
            transient_error_count=4,
        )
        assert result.success is False
        assert result.last_error == error


class TestRetryHandler:
    """Tests for RetryHandler."""

    @pytest.fixture
    def handler(self):
        """Create RetryHandler instance."""
        return RetryHandler(RetryConfig(max_retries=3, jitter=False))

    def test_calculate_delay_sequence(self, handler):
        """Test 2: Exponential backoff sequence 1s→2s→4s→8s→16s."""
        assert handler._calculate_delay(0) == 1.0
        assert handler._calculate_delay(1) == 2.0
        assert handler._calculate_delay(2) == 4.0
        assert handler._calculate_delay(3) == 8.0
        assert handler._calculate_delay(4) == 16.0

    def test_calculate_delay_capped(self, handler):
        """Test delay is capped at max_delay."""
        # Even for very high attempt numbers
        assert handler._calculate_delay(10) == 16.0

    def test_categorize_transient_errors(self, handler):
        """Test 4: Identifying transient vs permanent errors."""
        # Transient errors
        assert handler._is_transient(TransientError("timeout")) is True
        assert handler._is_transient(Exception("HTTP 429 Rate limit")) is True
        assert handler._is_transient(Exception("HTTP 503 Service unavailable")) is True
        assert handler._is_transient(Exception("Connection timeout")) is True

        # Permanent errors
        assert handler._is_transient(PermanentError("Unauthorized")) is False
        assert handler._is_transient(Exception("HTTP 401 Unauthorized")) is False
        assert handler._is_transient(Exception("HTTP 404 Not found")) is False
        assert handler._is_transient(Exception("HTTP 403 Forbidden")) is False

    @pytest.mark.asyncio
    async def test_retries_transient_errors(self, handler):
        """Test 1: RetryHandler retries transient errors up to max_retries."""
        call_count = 0

        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TransientError("Temporary error")
            return "success"

        result = await handler.execute(failing_func)

        assert result.success is True
        assert result.result == "success"
        assert result.attempts == 3
        assert result.transient_error_count == 2

    @pytest.mark.asyncio
    async def test_gives_up_after_max_retries(self, handler):
        """Test 3: RetryHandler gives up after max_retries and returns failure."""
        call_count = 0

        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise TransientError("Always fails")

        result = await handler.execute(always_failing)

        assert result.success is False
        assert result.attempts == 4  # 3 retries + 1 initial
        assert result.transient_error_count == 4

    @pytest.mark.asyncio
    async def test_permanent_error_fails_immediately(self, handler):
        """Test permanent errors fail immediately without retry."""
        call_count = 0

        async def auth_failure():
            nonlocal call_count
            call_count += 1
            raise PermanentError("Unauthorized")

        result = await handler.execute(auth_failure)

        assert result.success is False
        assert result.attempts == 1  # No retries
        assert result.permanent_error_count == 1
        assert call_count == 1  # Only called once

    @pytest.mark.asyncio
    async def test_records_retry_attempts_in_metadata(self, handler):
        """Test 5: RetryHandler records retry attempts in metadata."""
        call_count = 0

        async def transient_failure():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TransientError("First failure")
            return "ok"

        result = await handler.execute(transient_failure)

        assert result.success is True
        assert result.attempts == 2
        assert result.transient_error_count == 1
        assert result.total_delay_seconds > 0


class TestWithRetryDecorator:
    """Tests for @with_retry decorator."""

    @pytest.mark.asyncio
    async def test_decorator_applies_retry(self):
        """Test @with_retry decorator adds retry logic."""
        call_count = 0

        @with_retry(RetryConfig(max_retries=2, jitter=False))
        async def decorated_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TransientError("Temporary")
            return "decorated"

        result = await decorated_func()

        assert result.success is True
        assert result.result == "decorated"


class TestErrorCategory:
    """Tests for ErrorCategory enum."""

    def test_category_has_transient(self):
        """Test ErrorCategory has TRANSIENT."""
        assert ErrorCategory.TRANSIENT.value == "transient"

    def test_category_has_permanent(self):
        """Test ErrorCategory has PERMANENT."""
        assert ErrorCategory.PERMANENT.value == "permanent"
