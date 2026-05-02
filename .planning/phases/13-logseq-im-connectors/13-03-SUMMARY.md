---
phase: 13-logseq-im-connectors
plan: 03
subsystem: connectors
tags:
  - discord
  - gateway
  - websocket
  - reconnection
  - embeds
requires:
  - PHASE-10-connector-framework
  - PHASE-11-message-handler
provides:
  - DiscordConnector
  - DiscordMessage model
  - DiscordUser model
  - discord-ingestion-capability
key_decisions:
  - Gateway WebSocket for real-time messages
  - RESUME opcode for reconnection
  - Built-in rate limiting (50 req/sec)
  - Embed and attachment extraction
metrics:
  duration: 8m
  tests: 12
  files_created: 5
  completed_at: "2026-05-02"
---

# Phase 13 Plan 03: Discord Connector Summary

## One-liner

Discord connector via Gateway WebSocket with session resumption, embed extraction, and built-in rate limiting.

## Implementation

### Files Created

- `src/saw/connectors/im/discord/__init__.py` - Package exports
- `src/saw/connectors/im/discord/models.py` - DiscordMessage, DiscordUser
- `src/saw/connectors/im/discord/connector.py` - DiscordConnector

### Requirements Covered

| ID | Description | Status |
|----|-------------|--------|
| DISC-01 | Add Discord bot to server | Done |
| DISC-02 | Receive via Gateway WebSocket | Done |
| DISC-03 | Reconnection with resume | Done |
| DISC-04 | Embeds and attachments | Done |
| DISC-05 | 50 req/sec rate limit | Done |

## Key Decisions

1. **Gateway Model**: Uses discord.py's Gateway WebSocket for real-time message ingestion.

2. **Reconnection**: Session ID and sequence number stored for RESUME opcode on reconnect.

3. **Rate Limiting**: Built into discord.py library (50 req/sec global limit).

4. **Embeds**: Extracted into structured dict format for Claims metadata.

## Tests

12 unit tests covering:
- Connector protocol implementation
- Bot token authentication
- Message creation from discord.py objects
- Attachment extraction
- Embed extraction
- Thread and reply context
- Session tracking for resume

## Deviations

None - executed exactly as planned.
