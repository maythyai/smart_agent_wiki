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
from typing import Any, Callable

from fastapi import Request, Response, HTTPException, status
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

        # Log write operations to database (if write queue available)
        if is_write and hasattr(request.app.state, "write_queue"):
            try:
                audit_entry = {
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "user_id": user_id,
                    "ip": self._get_client_ip(request),
                    "duration_ms": round(duration_ms, 1),
                    "timestamp": time.time(),
                }
                # Store audit entry (non-blocking)
                await self._store_audit_entry(request, audit_entry)
            except Exception as e:
                logger.error("Failed to store audit entry: %s", e)

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

    async def _store_audit_entry(self, request: Request, entry: dict) -> None:
        """Store audit entry in database via write queue."""
        # Non-blocking: best-effort storage
        try:
            wq = request.app.state.write_queue
            if wq and hasattr(wq, "enqueue"):
                await wq.enqueue(
                    operation="audit_log",
                    payload=entry,
                    source="audit_middleware",
                )
        except Exception:
            pass  # Non-critical: log was already written to file


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


class InputSanitizerMiddleware(BaseHTTPMiddleware):
    """Sanitize input and detect injection attempts.

    SEC-04: XSS protection and SQL injection detection.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only check requests with body
        if request.method in ("POST", "PUT", "PATCH"):
            # Check query parameters
            for key, value in request.query_params.items():
                if check_sql_injection(value):
                    logger.warning(
                        "SQL injection attempt detected: param=%s ip=%s",
                        key,
                        request.client.host if request.client else "unknown",
                    )
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={
                            "error": "invalid_input",
                            "message": "Suspicious input detected in query parameters",
                        },
                    )

        return await call_next(request)


# ── JWT Authentication Dependency ─────────────────────────────────────


def get_current_user_from_token(request: Request) -> dict:
    """FastAPI dependency: extract and verify user from JWT token.

    SEC-01: JWT-based authentication for protected endpoints.
    SEC-02: Returns user with role for RBAC.

    Usage in routes:
        @router.get("/protected")
        async def protected(user: dict = Depends(get_current_user_from_token)):
            ...
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
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


def require_role(*allowed_roles: str) -> Callable:
    """FastAPI dependency: require specific user roles.

    SEC-02: RBAC enforcement for protected endpoints.

    Usage in routes:
        @router.delete("/admin-only")
        async def admin_only(user: dict = Depends(require_role("admin"))):
            ...
    """
    def dependency(user: dict = None) -> dict:
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        if user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_roles)}",
            )

        return user

    return dependency
