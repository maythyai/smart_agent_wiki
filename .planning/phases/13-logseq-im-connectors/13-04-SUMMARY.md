---
phase: 13-logseq-im-connectors
plan: 04
subsystem: connectors
tags:
  - feishu
  - wecom
  - chinese
  - webhooks
  - encryption
requires:
  - PHASE-10-connector-framework
  - PHASE-11-message-handler
provides:
  - FeishuConnector
  - WeComConnector
  - FeishuTokenManager
  - WeComCrypto
  - chinese-content-handling
key_decisions:
  - Multi-tenant token management for Feishu
  - AES-256-CBC encryption for WeCom
  - UTF-8 encoding for Chinese content
  - Webhook-based ingestion for both
metrics:
  duration: 12m
  tests: 17
  files_created: 13
  completed_at: "2026-05-02"
---

# Phase 13 Plan 04: Feishu + WeCom Connectors Summary

## One-liner

Feishu connector with multi-tenant token management and WeCom connector with AES-256-CBC encryption for Chinese enterprise messaging platforms.

## Implementation

### Feishu Files Created

- `src/saw/connectors/im/feishu/__init__.py` - Package exports
- `src/saw/connectors/im/feishu/models.py` - FeishuMessage, FeishuUser
- `src/saw/connectors/im/feishu/token_manager.py` - FeishuTokenManager
- `src/saw/connectors/im/feishu/event_handler.py` - FeishuEventHandler
- `src/saw/connectors/im/feishu/connector.py` - FeishuConnector

### WeCom Files Created

- `src/saw/connectors/im/wecom/__init__.py` - Package exports
- `src/saw/connectors/im/wecom/models.py` - WeComMessage
- `src/saw/connectors/im/wecom/crypto.py` - WeComCrypto
- `src/saw/connectors/im/wecom/connector.py` - WeComConnector

### Requirements Covered

| ID | Description | Status |
|----|-------------|--------|
| FEIS-01 | Install Feishu app via OAuth 2.0 | Done |
| FEIS-02 | Receive webhook events | Done |
| FEIS-03 | Multi-tenant token handling | Done |
| FEIS-04 | Wiki docs as content source | Done |
| FEIS-05 | Chinese content encoding | Done |
| WECO-01 | Configure webhook URL | Done |
| WECO-02 | Receive webhook messages | Done |
| WECO-03 | AES-256-CBC encryption | Done |
| WECO-04 | API rate limits | Done |

## Key Decisions

1. **Feishu Token Management**: Separate app_token and tenant_token with automatic refresh.

2. **WeCom Encryption**: AES-256-CBC with PKCS7 padding, SHA1 signature verification.

3. **Chinese Content**: All content handled as UTF-8; no GBK fallback needed.

4. **Wiki Docs**: Feishu Wiki doc events captured for ingestion as Claims.

## Tests

17 unit tests covering:
- Feishu connector implementation
- Multi-tenant token management
- Chinese content encoding
- WeCom connector implementation
- AES encryption/decryption
- Signature verification
- Webhook processing

## Deviations

None - executed exactly as planned.
