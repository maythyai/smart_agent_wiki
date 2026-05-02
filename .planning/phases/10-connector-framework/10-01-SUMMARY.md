---
phase: 10-connector-framework
plan: 01
subsystem: connectors
tags: [protocol, models, registry, rate-limiting]
dependency:
  requires: []
  provides: [UnifiedConnectorInterface, ConnectorRegistry, RateLimitManager]
  affects: []
tech-stack:
  added: []
  patterns: [Protocol, Singleton, Token Bucket]
key-files:
  created:
    - src/saw/connectors/__init__.py
    - src/saw/connectors/protocol.py
    - src/saw/connectors/models.py
    - src/saw/connectors/registry.py
    - src/saw/connectors/base_connector.py
    - src/saw/connectors/rate_limiter.py
    - src/saw/db/connector_models.py
  modified:
    - src/saw/db/__init__.py
decisions:
  - Protocol pattern for unified connector interface
  - Singleton pattern for connector registry
  - Token bucket algorithm for rate limiting
metrics:
  duration-min: 15
  completed: 2026-05-02
  tests-passed: 32
---

# Phase 10 Plan 01: Core Connector Protocol, Models, and Registry Summary

UnifiedConnectorInterface Protocol defines the contract for all third-party platform connectors with platform_name, supports_push, authenticate, get_items, put_item, delete_item, transform_to_claim, and transform_from_claim methods.

## Key Deliverables

- **SyncDirection enum**: PULL, PUSH, BIDIRECTIONAL for sync direction control
- **AuthResult dataclass**: access_token, refresh_token, expires_at, scopes for OAuth responses
- **ConnectorItem dataclass**: id, title, content, url, author, timestamps, metadata for platform items
- **UnifiedConnectorInterface Protocol**: Runtime-checkable Protocol for all connectors
- **TokenMasker**: Static utility masking tokens showing only last 4 characters (AUTH-04)
- **ConnectorConfig**: Dataclass for connector configuration with sync settings
- **SyncResult**: Dataclass for synchronization operation results
- **ConnectorStatus enum**: CONNECTED, DISCONNECTED, EXPIRED, ERROR for status tracking
- **RateLimitManager**: Token bucket algorithm for per-platform rate limiting (IM-06)
- **PlatformRateLimit**: Platform-specific rate limit configurations
- **ConnectorRegistry**: Singleton registry for connector management
- **BaseConnector**: Abstract base class with rate limiting integration
- **ConnectorConfigModel**: SQLAlchemy model for connector persistence
- **ConnectorSyncLog**: SQLAlchemy model for sync operation logging

## Requirements Addressed

- AUTH-04: Token masking in logs/API responses (last 4 chars only)
- IM-06: Per-platform rate limits with token bucket algorithm

## Deviations from Plan

None - plan executed exactly as written.

## Test Results

```
32 passed in 1.36s
```

All tests pass covering protocol definitions, model creation, registry operations, and rate limiting behavior.
