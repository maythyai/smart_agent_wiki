"""Retry handling with exponential backoff for transient failures.

Plan 11-02: Backpressure, retry, and health status.
Per ERRO-01: Exponential backoff 1s→2s→4s→8s→16s (max 5 retries).
"""
from __future__ import annotations

import asyncio
import enum
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Generic, Optional, TypeVar

T = TypeVar("T")


def utcnow() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


class RetryConfig:
    """Configuration for retry handling.

    Attributes:
        max_retries: Maximum number of retry attempts.
        base_delay_seconds: Initial delay before first retry.
        max_delay_seconds: Maximum delay cap.
        exponential_base: Multiplier for exponential backoff.
        jitter: Add random jitter to prevent thundering herd.
    """

    def __init__(
        self,
        max_retries: int = 5,
        base_delay_seconds: float = 1.0,
        max_delay_seconds: float = 16.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.exponential_base = exponential_base
        self.jitter = jitter


@dataclass
class RetryResult(Generic[T]):
    """Result of a retry operation.

    Attributes:
        success: Whether the operation eventually succeeded.
        result: The result value if successful.
        attempts: Number of attempts made.
        total_delay_seconds: Total time spent waiting.
        last_error: The last error encountered.
        transient_error_count: Number of transient errors.
        permanent_error_count: Number of permanent errors.
    """

    success: bool
    result: Optional[T] = None
    attempts: int = 0
    total_delay_seconds: float = 0.0
    last_error: Optional[Exception] = None
    transient_error_count: int = 0
    permanent_error_count: int = 0


class TransientError(Exception):
    """Error that should be retried (rate limits, timeouts, 5xx)."""

    def __init__(self, message: str, retry_after: Optional[float] = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after  # Seconds to wait from Retry-After header


class PermanentError(Exception):
    """Error that should not be retried (auth failures, 4xx)."""
    pass


class ErrorCategory(enum.Enum):
    """Category of error for retry decision."""
    TRANSIENT = "transient"
    PERMANENT = "permanent"


class RetryHandler:
    """Handles retry logic with exponential backoff.

    Per ERRO-01: Exponential backoff 1s→2s→4s→8s→16s (max 5 retries).

    Transient errors (429, 500, 502, 503, 504, timeouts) are retried.
    Permanent errors (401, 403, 404, 400) fail immediately.
    """

    # HTTP status codes that are transient
    TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}

    # HTTP status codes that are permanent
    PERMANENT_STATUS_CODES = {400, 401, 403, 404}

    def __init__(self, config: Optional[RetryConfig] = None) -> None:
        """Initialize retry handler.

        Args:
            config: Retry configuration.
        """
        self._config = config or RetryConfig()

    def _calculate_delay(self, attempt: int, error: Optional[Exception] = None) -> float:
        """Calculate delay before next retry.

        Uses exponential backoff: base * (exponential_base ^ attempt)
        Capped at max_delay.
        Adds jitter if enabled.

        Args:
            attempt: Current attempt number (0-indexed).
            error: The error that triggered retry (for retry_after).

        Returns:
            Delay in seconds.
        """
        # Check for Retry-After header
        if isinstance(error, TransientError) and error.retry_after:
            return min(error.retry_after, self._config.max_delay_seconds)

        # Calculate exponential delay
        delay = self._config.base_delay_seconds * (
            self._config.exponential_base ** attempt
        )

        # Cap at max
        delay = min(delay, self._config.max_delay_seconds)

        # Add jitter (±25%)
        if self._config.jitter:
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0.1, delay)  # Minimum delay

        return delay

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error as transient or permanent.

        Args:
            error: The error to categorize.

        Returns:
            ErrorCategory enum value.
        """
        # Known error types
        if isinstance(error, TransientError):
            return ErrorCategory.TRANSIENT
        if isinstance(error, PermanentError):
            return ErrorCategory.PERMANENT

        # Check for HTTP status codes in error
        error_str = str(error).lower()
        status_code = self._extract_status_code(error_str)

        if status_code:
            if status_code in self.TRANSIENT_STATUS_CODES:
                return ErrorCategory.TRANSIENT
            if status_code in self.PERMANENT_STATUS_CODES:
                return ErrorCategory.PERMANENT

        # Check for common transient error patterns
        transient_patterns = [
            "timeout",
            "connection reset",
            "connection refused",
            "rate limit",
            "too many requests",
            "temporarily unavailable",
            "service unavailable",
            "bad gateway",
            "gateway timeout",
        ]

        for pattern in transient_patterns:
            if pattern in error_str:
                return ErrorCategory.TRANSIENT

        # Default to permanent for safety
        return ErrorCategory.PERMANENT

    def _extract_status_code(self, error_str: str) -> Optional[int]:
        """Extract HTTP status code from error string.

        Args:
            error_str: Error message string.

        Returns:
            Status code if found, None otherwise.
        """
        import re
        match = re.search(r"\b([45]\d{2})\b", error_str)
        if match:
            return int(match.group(1))
        return None

    def _is_transient(self, error: Exception) -> bool:
        """Check if error is transient (should retry).

        Args:
            error: The error to check.

        Returns:
            True if transient, False if permanent.
        """
        return self._categorize_error(error) == ErrorCategory.TRANSIENT

    async def execute(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> RetryResult[T]:
        """Execute async function with retry logic.

        Args:
            func: Async function to execute.
            *args: Positional arguments for func.
            **kwargs: Keyword arguments for func.

        Returns:
            RetryResult with operation outcome.
        """
        result = RetryResult[T](success=False, attempts=0)
        last_error: Optional[Exception] = None

        for attempt in range(self._config.max_retries + 1):
            result.attempts = attempt + 1

            try:
                value = await func(*args, **kwargs)
                result.success = True
                result.result = value
                return result

            except Exception as e:
                last_error = e

                if isinstance(e, PermanentError):
                    result.permanent_error_count += 1
                    result.last_error = e
                    return result

                if not self._is_transient(e):
                    result.permanent_error_count += 1
                    result.last_error = e
                    return result

                result.transient_error_count += 1

                # Check if we have retries left
                if attempt < self._config.max_retries:
                    delay = self._calculate_delay(attempt, e)
                    result.total_delay_seconds += delay
                    await asyncio.sleep(delay)

        # All retries exhausted
        result.last_error = last_error
        return result


def with_retry(
    config: Optional[RetryConfig] = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[RetryResult[T]]]]:
    """Decorator for adding retry logic to async functions.

    Args:
        config: Retry configuration.

    Returns:
        Decorated function with retry logic.
    """
    handler = RetryHandler(config)

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[RetryResult[T]]]:
        async def wrapper(*args: Any, **kwargs: Any) -> RetryResult[T]:
            return await handler.execute(func, *args, **kwargs)
        return wrapper

    return decorator
