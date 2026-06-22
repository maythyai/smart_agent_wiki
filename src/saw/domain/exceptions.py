"""Domain exceptions hierarchy."""
from __future__ import annotations


class SAWError(Exception):
    """Base exception for all Smart Agent Wiki errors."""


class StorageError(SAWError):
    """Base for storage-related errors."""


class WriteQueueError(SAWError):
    """Write Queue operation failed."""


class VaultError(StorageError):
    """Vault storage operation failed."""


class ClaimsDBError(StorageError):
    """Claims DB operation failed."""


class FTS5Error(StorageError):
    """FTS5 index operation failed."""


class ConfigError(SAWError):
    """Configuration error."""


class LLMError(SAWError):
    """LLM call or response parsing failed."""


class ConnectorError(SAWError):
    """Base for all connector errors."""


class AuthenticationError(ConnectorError):
    """OAuth/auth failures."""


class SyncError(ConnectorError):
    """Sync operation failures."""


class TransientError(ConnectorError):
    """Temporary/retryable errors."""


class PermanentError(ConnectorError):
    """Permanent/non-retryable errors."""


class TokenRefreshError(ConnectorError):
    """Token refresh failures."""


class PipelineError(SAWError):
    """Ingest pipeline errors."""


class RateLimitError(SAWError):
    """Rate limiting errors."""

