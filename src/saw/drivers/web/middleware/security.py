"""Security middleware for production hardening.

Phase 39: Security Hardening.
- SEC-05: CORS policy (handled by FastAPI CORSMiddleware in app.py)
- SEC-08: Security headers (CSP, HSTS, X-Frame-Options)
- SEC-07: Audit logging middleware
- SEC-04: Input sanitization middleware
- JWT authentication middleware (dependency injection)
"""
from __future__ import annotations

import logging
import re
import time
from typing import Callable

from fastapi import Request, Response, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# ── SEC-08: Security Headers Middleware ──────────────────────────────


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses.

    SEC-08: Content-Security-Policy, HSTS, X-Frame-Options, etc.
    """

    def __init__(
        self,
        app,
        csp_policy: str | None = None,
        hsts_max_age: int = 31536000,
    ):
        super().__init__(app)
        self.csp_policy = csp_policy or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'"
        )
        self.hsts_max_age = hsts_max_age

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Content-Security-Policy
        response.headers["Content-Security-Policy"] = self.csp_policy

        # HTTP Strict Transport Security
        response.headers["Strict-Transport-Security"] = (
            f"max-age={self.hsts_max_age}; includeSubDomains"
        )

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy (restrict browser features)
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        return response


# ── SEC-07: Audit Logging Middleware ──────────────────────────────────


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Log all API requests for audit trail.

    SEC-07: Records method, path, status, user, and timing.
    """

    # Paths to skip audit logging
    SKIP_PATHS = {"/health", "/health/live", "/health/ready", "/metrics"}

    # Methods that modify state (write operations)
    WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip non-API and health check paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start_time = time.time()

        # Extract user info from JWT (if present)
        user_id = self._extract_user_id(request)

        # Process request
        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        # Log the request
        is_write = request.method in self.WRITE_METHODS
        log_level = logging.INFO if not is_write else logging.WARNING

        logger.log(
            log_level,
            "AUDIT: %s %s -> %d (%.1fms) user=%s ip=%s",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            user_id or "anonymous",
            self._get_client_ip(request),
        )

        # Audit records are persisted by the dedicated AuditService (Ed25519-
        # signed, SQLAlchemy-backed) which is intentionally independent of
        # the claims Write Queue: an outbox failure must never lose the
        # audit trail of that failure. Routing audit writes through the
        # observed outbox would violate that principle, so we do not do it
        # here.

        return response

    def _extract_user_id(self, request: Request) -> str | None:
        """Extract user ID from JWT token in Authorization header."""
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]
        try:
            from saw.auth.jwt_auth import JWTHandler, AuthConfig
            handler = JWTHandler(AuthConfig.from_env())
            token_data = handler.verify_access_token(token)
            return token_data.sub
        except Exception:
            return None

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.headers.get(
            "X-Real-IP",
            request.client.host if request.client else "unknown",
        )


# ── SEC-04: Input Sanitization Middleware ─────────────────────────────


# Dangerous patterns for XSS and injection
_XSS_PATTERNS = [
    re.compile(r"<script[^>]*>", re.IGNORECASE),
    re.compile(r"javascript:", re.IGNORECASE),
    re.compile(r"on\w+\s*=", re.IGNORECASE),  # onclick=, onload=, etc.
    re.compile(r"<iframe[^>]*>", re.IGNORECASE),
    re.compile(r"<object[^>]*>", re.IGNORECASE),
]

_SQL_INJECTION_PATTERNS = [
    re.compile(r"(\b(union\s+select|drop\s+table|insert\s+into)\b)", re.IGNORECASE),
    re.compile(r"(--|;)\s*$", re.IGNORECASE),
    re.compile(r"'\s*(or|and)\s+'?\d+'?\s*=\s*'?\d+", re.IGNORECASE),
]


def sanitize_string(value: str) -> str:
    """Sanitize a string value against XSS and injection.

    SEC-04: Strips dangerous HTML tags and patterns.
    """
    if not isinstance(value, str):
        return value

    sanitized = value

    # Strip dangerous HTML patterns
    for pattern in _XSS_PATTERNS:
        sanitized = pattern.sub("", sanitized)

    return sanitized


def check_sql_injection(value: str) -> bool:
    """Check if a string contains SQL injection patterns.

    Returns True if suspicious patterns are found.
    """
    if not isinstance(value, str):
        return False

    for pattern in _SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            return True

    return False


def check_xss(value: str) -> bool:
    """Check if a string contains clear XSS patterns.

    F-AUTH-06: narrower than ``sanitize_string`` (which also strips
    ``onload=``-style attributes that can appear in legitimate text) so it
    can be used to *reject* suspicious query input without false positives.
    """
    if not isinstance(value, str):
        return False
    # _XSS_PATTERNS: 0=<script>, 1=javascript:, 2=on\w+=, 3=<iframe>, 4=<object>
    for pattern in (_XSS_PATTERNS[0], _XSS_PATTERNS[1], _XSS_PATTERNS[3], _XSS_PATTERNS[4]):
        if pattern.search(value):
            return True
    return False


class InputSanitizerMiddleware(BaseHTTPMiddleware):
    """Sanitize input and detect injection attempts.

    SEC-04: XSS protection and SQL injection detection.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # F-AUTH-06: check query parameters on ALL methods (previously only
        # POST/PUT/PATCH and only SQL injection). sanitize_string/check_xss
        # are now actually used. Request-body XSS is mitigated at the
        # Pydantic schema + render layers (a dedicated body sanitizer is a
        # follow-up — body streams can't be safely rewritten in middleware).
        client_ip = request.client.host if request.client else "unknown"
        for key, value in request.query_params.items():
            if check_sql_injection(value):
                logger.warning(
                    "SQL injection attempt detected: param=%s ip=%s",
                    key,
                    client_ip,
                )
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "invalid_input",
                        "message": "Suspicious input detected in query parameters",
                    },
                )
            if check_xss(value):
                logger.warning(
                    "XSS pattern in query parameter: param=%s ip=%s",
                    key,
                    client_ip,
                )
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={
                        "error": "invalid_input",
                        "message": "Disallowed HTML in query parameters",
                    },
                )

        return await call_next(request)


# ── JWT Authentication Dependency ─────────────────────────────────────


def get_current_user_from_token(request: Request) -> dict:
    """FastAPI dependency: extract and verify user from JWT token or API key.

    SEC-01: JWT-based authentication for protected endpoints.
    SEC-02: Returns user with role for RBAC.

    Supports two authentication schemes:
    - ``Authorization: Bearer <jwt>`` — the standard JWT path
    - ``Authorization: ApiKey <key>`` — single-user API key path (Mode A)

    Usage in routes:
        @router.get("/protected")
        async def protected(user: dict = Depends(get_current_user_from_token)):
            ...
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if auth_header.startswith("ApiKey "):
        # SEC (CR-1): verify the API key against the database. The previous
        # implementation returned role="admin" for any non-empty ApiKey header
        # without any DB lookup — a direct auth bypass in team mode.
        api_key_str = auth_header[7:].strip()
        if not api_key_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Empty API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        from saw.api.keys import verify_api_key_sync
        api_key = verify_api_key_sync(api_key_str)
        if api_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        _perms = set(
            p.strip() for p in (api_key.permissions or "").split(",") if p.strip()
        )
        _role = "admin" if "admin" in _perms else ("editor" if "write" in _perms else "viewer")
        return {
            "user_id": api_key.user_id,
            "role": _role,
            "token": api_key_str,
        }

    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer ' or 'ApiKey '",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header[7:]

    try:
        from saw.auth.jwt_auth import JWTHandler, AuthConfig
        handler = JWTHandler(AuthConfig.from_env())
        token_data = handler.verify_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": token_data.sub,
        "role": token_data.role,
        "token": token,
    }


def get_current_user_local(request: Request) -> dict:
    """Local-trust dependency (single-user desktop mode).

    If a valid Bearer JWT or ApiKey is present, honour it.  When no
    token is supplied the request is trusted as a local admin —
    preserving the pre-auth single-user behaviour where ``saw web``
    has no registered users.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return {"user_id": "local", "role": "admin", "token": None}
    if auth_header.startswith("ApiKey "):
        # P2: API key — trust the header in local mode (rate limiter
        # handles actual verification via get_api_key_func).
        return {"user_id": "api-key-user", "role": "admin", "token": auth_header[7:]}
    # Bearer token path — delegate to the JWT verifier
    return get_current_user_from_token(request)


def get_current_user(request: Request) -> dict:
    """Mode-aware authentication dependency.

    Reads ``request.app.state.auth_mode`` (set by ``create_app``):

    * ``"team"``  → require a valid JWT (``get_current_user_from_token``)
    * ``"local"`` → trust local requests, honour a JWT if supplied

    Default is ``"local"`` so existing single-user / CLI usage is
    unchanged. This is the dependency protected routers attach.
    """
    mode = getattr(request.app.state, "auth_mode", "local")
    if mode == "team":
        return get_current_user_from_token(request)
    return get_current_user_local(request)


def require_role(*allowed_roles: str) -> Callable:
    """FastAPI dependency factory: require specific user roles.

    SEC-02: RBAC enforcement for protected endpoints.

    Resolves the current user via :func:`get_current_user` (mode-aware)
    and rejects with 403 if the user's role is not in ``allowed_roles``.

    Usage in routes:
        @router.delete("/admin-only")
        async def admin_only(user: dict = Depends(require_role("admin"))):
            ...
    """
    def dependency(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed_roles:
            # F-AUTH-05: do not leak internal role names to the client.
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return user

    return dependency
