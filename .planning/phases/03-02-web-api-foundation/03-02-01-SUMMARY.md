---
phase: 03-02-web-api-foundation
plan: 01
subsystem: api
tags: [fastapi, websocket, cors, rfc-7807, middleware]

requires:
  - phase: 03-01-multi-agent-foundation
    provides: CollaborateEngine, QueryEngine, WriteQueue for dependency injection
provides:
  - FastAPI Application Factory with dependency injection
  - WebSocket ConnectionManager for real-time updates
  - CORS middleware for frontend development
  - RFC 7807 Problem Details error handlers
affects: [03-02-02, 03-02-03, 03-03]

tech-stack:
  added: [fastapi, pydantic, uvicorn, httpx, pytest-asyncio]
  patterns:
    - Application Factory pattern
    - Dependency injection via app.state
    - RFC 7807 Problem Details for error responses
    - WebSocket connection management with session grouping

key-files:
  created:
    - src/saw/drivers/web/__init__.py
    - src/saw/drivers/web/app.py
    - src/saw/drivers/web/websocket.py
    - src/saw/drivers/web/middleware/__init__.py
    - src/saw/drivers/web/middleware/cors.py
    - src/saw/drivers/web/middleware/errors.py
    - src/saw/drivers/web/routes/__init__.py
    - src/saw/drivers/web/routes/websocket.py
    - src/saw/drivers/web/schemas/__init__.py
    - src/saw/drivers/web/schemas/websocket.py
    - tests/unit/drivers/web/__init__.py
    - tests/unit/drivers/web/test_app_factory.py
    - tests/unit/drivers/web/test_websocket.py
  modified: []

key-decisions:
  - "D-01: FastAPI server with RESTful API and WebSocket support"
  - "D-02: CLI command `saw web` starts server on port 8000"
  - "D-03: CORS allows localhost:3000 for frontend development"
  - "D-04: WebSocket endpoint at /ws/{session_id} for real-time updates"
  - "D-05: Event types: agent_status, workflow_progress, page_updated"
  - "D-06: Connection management with heartbeat and limits"

patterns-established:
  - "Application Factory: create_app() injects QueryEngine, CollaborateEngine, WriteQueue"
  - "WebSocket ConnectionManager: session-based grouping with connection limits (10 per session)"
  - "RFC 7807 errors: All errors return type, title, status, detail fields"
  - "Event mapping: Domain events converted to WebSocket messages via _event_to_message"

requirements-completed: [WEB-01]

duration: 15min
completed: "2026-04-29"
---

# Phase 03-02 Plan 01: Web API Foundation Summary

**FastAPI Application Factory with WebSocket ConnectionManager, CORS middleware, and RFC 7807 error handlers**

## Performance

- **Duration:** 15 min
- **Started:** 2026-04-29T00:16:28Z
- **Completed:** 2026-04-29T00:31:00Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- FastAPI Application Factory with dependency injection for QueryEngine, CollaborateEngine, WriteQueue
- WebSocket ConnectionManager with session-based grouping and connection limits (10 per session)
- CORS middleware configured for localhost:3000 frontend development
- RFC 7807 Problem Details error handlers for SAWError, ValidationError, and generic exceptions
- WebSocket endpoint at /ws/{session_id} with ping/pong heartbeat support
- Event-to-message mapping for agent_status, workflow_progress, page_updated

## Task Commits

Each task was committed atomically:

1. **Task 1: Application Factory and Middleware** - `ee17625` (feat)
2. **Task 2: WebSocket ConnectionManager and endpoint** - `1dbfd3f` (feat)

## Files Created/Modified
- `src/saw/drivers/web/__init__.py` - Package init, exports create_app
- `src/saw/drivers/web/app.py` - Application Factory with lifespan management
- `src/saw/drivers/web/websocket.py` - ConnectionManager and WSMessage
- `src/saw/drivers/web/middleware/cors.py` - CORS configuration helpers
- `src/saw/drivers/web/middleware/errors.py` - RFC 7807 error handlers
- `src/saw/drivers/web/routes/websocket.py` - WebSocket endpoint
- `src/saw/drivers/web/schemas/websocket.py` - WebSocket message schemas
- `tests/unit/drivers/web/test_app_factory.py` - 11 tests for app factory
- `tests/unit/drivers/web/test_websocket.py` - 20 tests for WebSocket

## Decisions Made
- Used Application Factory pattern for testability (create_app() with injected dependencies)
- WebSocket connections grouped by session_id for targeted broadcasts
- Connection limit of 10 per session to prevent resource exhaustion (T-03-02-02 mitigation)
- Enum values serialized using .value for string enums (e.g., Status.RUNNING -> "running")
- Generic errors return "An unexpected error occurred" without stack traces (T-03-02-04 mitigation)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed CORS middleware test assertion**
- **Found during:** Task 1 (test execution)
- **Issue:** Test checked for "CORSMiddleware" in type string but FastAPI wraps middleware in Middleware objects with cls attribute
- **Fix:** Updated test to check middleware.cls instead of type string
- **Files modified:** tests/unit/drivers/web/test_app_factory.py
- **Verification:** Test passes
- **Committed in:** ee17625 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed generic error handler test**
- **Found during:** Task 1 (test execution)
- **Issue:** TestClient's default behavior re-raises exceptions, bypassing our error handler
- **Fix:** Used TestClient with raise_server_exceptions=False to let our handler catch the exception
- **Files modified:** tests/unit/drivers/web/test_app_factory.py
- **Verification:** Test passes, RFC 7807 format returned
- **Committed in:** ee17625 (Task 1 commit)

**3. [Rule 1 - Bug] Fixed event test with class attributes**
- **Found during:** Task 2 (test execution)
- **Issue:** Mock events used class attributes instead of instance attributes, which don't appear in __dict__
- **Fix:** Changed mock events to use __init__ for instance attributes
- **Files modified:** tests/unit/drivers/web/test_websocket.py
- **Verification:** All 20 WebSocket tests pass
- **Committed in:** 1dbfd3f (Task 2 commit)

**4. [Rule 1 - Bug] Fixed enum serialization to use .value**
- **Found during:** Task 2 (test execution)
- **Issue:** String enums returned .name (e.g., "RUNNING") instead of .value (e.g., "running")
- **Fix:** Changed _event_to_payload to use isinstance(value, Enum) check and value.value
- **Files modified:** src/saw/drivers/web/websocket.py
- **Verification:** Enum test passes with correct value
- **Committed in:** 1dbfd3f (Task 2 commit)

---

**Total deviations:** 4 auto-fixed (4 bugs)
**Impact on plan:** All auto-fixes were test/serialization correctness issues. No scope creep.

## Issues Encountered
- FastAPI TestClient behavior with exception handlers requires raise_server_exceptions=False
- Python class attributes vs instance attributes in __dict__ for dataclasses

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Web API foundation ready for REST endpoints (Search API, Graph API, Page API)
- WebSocket infrastructure in place for real-time updates
- All 31 unit tests passing

---
*Phase: 03-02-web-api-foundation*
*Completed: 2026-04-29*
