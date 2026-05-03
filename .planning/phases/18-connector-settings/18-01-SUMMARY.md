---
phase: 18-connector-settings
plan: 01
subsystem: api
tags: [settings, persistence, rest-api, validation]
requires: [CONF-02, CONF-03, CONF-05, CONF-07]
provides: [settings-api, settings-persistence, oauth-reauth]
affects: [connector-configuration]
tech_stack:
  added: [sqlalchemy-model, pydantic-validation, fastapi-router]
  patterns: [rest-crud, field-validator, session-dependency]
key_files:
  created: [src/saw/db/connector_settings.py, src/saw/api/connector_settings.py, tests/api/test_connector_settings.py]
  modified: [src/saw/api/__init__.py, src/saw/drivers/web/app.py]
decisions:
  - D-01: Dedicated settings table with platform as primary key
  - D-07: Named interval modes instead of seconds
  - D-09-D-11: Three sync direction modes
metrics:
  duration_minutes: 15
  completed_date: "2026-05-03"
  tasks_completed: 3
  files_created: 3
  files_modified: 2
  tests_added: 16
---

# Phase 18 Plan 01: Settings API and Persistence Summary

Implemented per-connector configuration persistence layer and REST API endpoints. Settings are stored in a dedicated database table with platform as primary key, allowing one settings row per connector.

## Implementation Details

### Database Model (Task 1)

Created `ConnectorSettingsModel` in `src/saw/db/connector_settings.py`:
- `platform`: String(50) — primary key, one row per connector
- `sync_interval`: String(20) — named interval mode ("5min", "15min", "1hr", "6hr", "manual")
- `sync_directions`: String(20) — sync direction mode ("inbound_only", "outbound_only", "bidirectional")
- `rate_limit_override`: Integer (nullable) — per CONF-05 safety bounds 1-100
- `property_mappings`: Text (JSON) — stores field-to-property mappings
- `updated_at`: DateTime(timezone=True) — last modification timestamp

### API Endpoints (Task 2)

Created router in `src/saw/api/connector_settings.py`:

1. **GET /api/v1/connectors/{platform}/settings**
   - Returns current settings for platform
   - Returns defaults if no settings exist yet
   - Response: `SettingsResponse` with all fields

2. **PUT /api/v1/connectors/{platform}/settings**
   - Updates settings for platform
   - Validates against whitelist per D-07, D-09-D-11
   - Rate limit bounds validation (1-100)
   - Returns updated settings confirming save

3. **POST /api/v1/connectors/{platform}/reauth**
   - Returns OAuth re-authorization URL
   - Delegates to existing OAuth handler
   - Only for OAuth-based platforms

### Test Coverage (Task 3)

16 tests in `tests/api/test_connector_settings.py`:
- `test_get_settings_existing` — returns stored settings
- `test_get_settings_default` — returns defaults for new connector
- `test_update_settings_valid` — valid values return 200
- `test_update_settings_invalid_interval` — invalid sync_interval returns 400
- `test_update_settings_invalid_direction` — invalid sync_directions returns 400
- `test_update_settings_rate_limit_bounds` — bounds checking for rate_limit
- `test_settings_persist` — PUT then GET returns same values
- Reauth tests for URL generation and error handling

## Deviations from Plan

None — plan executed exactly as written.

## Verification

```bash
# Run tests
pytest tests/api/test_connector_settings.py -v
# Result: 16 passed in 2.85s

# Manual GET test
curl http://localhost:8000/api/v1/connectors/notion/settings

# Manual PUT test
curl -X PUT -H "Content-Type: application/json" \
  -d '{"sync_interval":"15min"}' \
  http://localhost:8000/api/v1/connectors/notion/settings
```

## Commits

| Commit | Message |
|--------|---------|
| 87741ad | feat(18-01): create ConnectorSettingsModel database model |
| 2a83631 | feat(18-01): create Settings API endpoints |
| fcd466f | test(18-01): add connector settings API tests |

## Self-Check: PASSED

- [x] `src/saw/db/connector_settings.py` exists
- [x] `src/saw/api/connector_settings.py` exists
- [x] `tests/api/test_connector_settings.py` exists
- [x] All 16 tests pass
- [x] Commits 87741ad, 2a83631, fcd466f verified in git log