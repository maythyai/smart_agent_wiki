"""Observability middleware + init: request-id propagation, structured
logging, and optional Sentry (HI-16).

Previously the app had no request-level correlation ID (a trace_id existed
only inside the A2A agent protocol), no Sentry integration, and only
plain-text logs. This module:

* ``RequestContextMiddleware`` — reads or generates ``X-Request-Id`` per
  request, stores it in a ``ContextVar`` so any log line emitted during the
  request (including in the Write Queue dispatcher thread, which inherits the
  contextvar) carries it, and echoes it back on the response.
* ``init_observability()`` — attaches a request-id log filter (always) and a
  JSON formatter (opt-in via ``SAW_JSON_LOGS=1`` or team mode), and initialises
  Sentry when ``SENTRY_DSN`` is set (no-op if ``sentry_sdk`` is absent).
"""
from __future__ import annotations

import contextvars
import json
import logging
import os
import uuid
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Per-request correlation ID, inheritable by background tasks/threads spawned
# via asyncio (and by threadpool tasks that copy context).
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "saw_request_id", default="-"
)


class _RequestIdFilter(logging.Filter):
    """Stamp every log record with the current request_id (default "-")."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Propagate/generate ``X-Request-Id`` across the request lifecycle (HI-16)."""

    HEADER = "X-Request-Id"

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        rid = request.headers.get(self.HEADER) or uuid.uuid4().hex
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers[self.HEADER] = rid
        return response


class JsonFormatter(logging.Formatter):
    """Minimal structured (JSON) log formatter for team/production mode."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def init_observability(auth_mode: str = "local") -> None:
    """HI-16: attach request-id logging + optional Sentry + JSON logs.

    Safe to call multiple times — avoids adding duplicate handlers.
    """
    root = logging.getLogger()

    # 1) Always stamp records with request_id (cheap, no format change).
    if not any(
        isinstance(h, logging.Handler) and any(
            isinstance(f, _RequestIdFilter) for f in h.filters
        )
        for h in root.handlers
    ):
        # Attach the filter to existing handlers; if there are none, create one.
        if not root.handlers:
            h = logging.StreamHandler()
            root.addHandler(h)
        for h in root.handlers:
            if not any(isinstance(f, _RequestIdFilter) for f in h.filters):
                h.addFilter(_RequestIdFilter())

    # 2) Structured (JSON) logging — production default (SPEC-F-D-3).
    #    Previously opt-in (SAW_JSON_LOGS=1 or team mode only); now ON by
    #    default so team/prod deployments get structured logs without extra
    #    config.  Local dev opts back into readable text via SAW_PRETTY_LOGS=1
    #    or SAW_JSON_LOGS=0.  Backward compat: SAW_JSON_LOGS=1 still forces ON.
    saw_json = os.environ.get("SAW_JSON_LOGS", "").lower()
    saw_pretty = os.environ.get("SAW_PRETTY_LOGS", "").lower()
    if saw_pretty == "1":
        want_json = False
    elif saw_json == "0":
        want_json = False
    elif saw_json == "1":
        want_json = True
    else:
        want_json = True  # production default
    # Team mode always forces JSON regardless of the local-dev overrides.
    if auth_mode == "team":
        want_json = True
    if want_json and not any(
        isinstance(h, logging.StreamHandler) and isinstance(h.formatter, JsonFormatter)
        for h in root.handlers
    ):
        for h in root.handlers:
            h.setFormatter(JsonFormatter())

    # 3) Optional Sentry (env-gated; no-op if sentry_sdk is not installed).
    dsn = os.environ.get("SENTRY_DSN")
    if dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(
                dsn=dsn,
                environment=os.environ.get("SAW_ENV", auth_mode),
                traces_sample_rate=float(
                    os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")
                ),
            )
            logging.getLogger(__name__).info("Sentry initialised (env=%s)", auth_mode)
        except ImportError:
            logging.getLogger(__name__).warning(
                "SENTRY_DSN set but sentry_sdk not installed; skipping."
            )
        except Exception as e:  # pragma: no cover — never block startup on telemetry
            logging.getLogger(__name__).warning("Sentry init failed: %s", e)
