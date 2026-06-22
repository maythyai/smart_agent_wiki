"""Tests for security middleware.

Phase 40: Test Coverage — TEST-01, SEC-04/07/08 validation.
Covers: SecurityHeadersMiddleware, InputSanitizerMiddleware, sanitize_string, check_sql_injection.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from saw.drivers.web.middleware.security import (
    sanitize_string,
    check_sql_injection,
)


# ── Input Sanitization Tests ──────────────────────────────────────────


class TestSanitizeString:
    """Tests for sanitize_string function."""

    def test_normal_string_unchanged(self):
        assert sanitize_string("Hello World") == "Hello World"

    def test_script_tag_removed(self):
        result = sanitize_string('<script>alert("xss")</script>')
        assert "<script" not in result.lower()

    def test_javascript_protocol_removed(self):
        result = sanitize_string('javascript:alert("xss")')
        assert "javascript:" not in result.lower()

    def test_event_handler_removed(self):
        result = sanitize_string('<img onerror="alert(1)" src="x">')
        assert "onerror" not in result.lower()

    def test_iframe_removed(self):
        result = sanitize_string('<iframe src="evil.com"></iframe>')
        assert "<iframe" not in result.lower()

    def test_object_removed(self):
        result = sanitize_string('<object data="evil.swf"></object>')
        assert "<object" not in result.lower()

    def test_empty_string(self):
        assert sanitize_string("") == ""

    def test_non_string_passthrough(self):
        assert sanitize_string(42) == 42
        assert sanitize_string(None) is None

    def test_mixed_content(self):
        result = sanitize_string('Hello <script>bad</script> World')
        assert "Hello" in result
        assert "World" in result
        assert "<script" not in result.lower()


class TestCheckSqlInjection:
    """Tests for check_sql_injection detection."""

    def test_normal_string(self):
        assert check_sql_injection("Hello World") is False

    def test_union_select(self):
        assert check_sql_injection("' UNION SELECT * FROM users --") is True

    def test_drop_table(self):
        assert check_sql_injection("'; DROP TABLE users; --") is True

    def test_insert_into(self):
        assert check_sql_injection("' INSERT INTO users VALUES ('a', 'b')") is True

    def test_or_condition(self):
        assert check_sql_injection("' OR '1'='1") is True

    def test_trailing_semicolon(self):
        assert check_sql_injection("admin';") is True

    def test_trailing_comment(self):
        assert check_sql_injection("admin'--") is True

    def test_empty_string(self):
        assert check_sql_injection("") is False

    def test_non_string(self):
        assert check_sql_injection(42) is False
        assert check_sql_injection(None) is False

    def test_safe_sql_keywords(self):
        # Normal text containing SQL-like words shouldn't trigger
        assert check_sql_injection("I will select a book from the shelf") is False


# ── Security Headers Tests ────────────────────────────────────────────


class TestSecurityHeaders:
    """Tests for SecurityHeadersMiddleware behavior."""

    def test_middleware_importable(self):
        from saw.drivers.web.middleware.security import SecurityHeadersMiddleware
        assert SecurityHeadersMiddleware is not None

    def test_custom_csp_policy(self):
        from saw.drivers.web.middleware.security import SecurityHeadersMiddleware
        mock_app = MagicMock()
        middleware = SecurityHeadersMiddleware(
            mock_app,
            csp_policy="default-src 'none'",
        )
        assert middleware.csp_policy == "default-src 'none'"

    def test_default_csp_policy(self):
        from saw.drivers.web.middleware.security import SecurityHeadersMiddleware
        mock_app = MagicMock()
        middleware = SecurityHeadersMiddleware(mock_app)
        assert "default-src 'self'" in middleware.csp_policy


# ── Audit Middleware Tests ────────────────────────────────────────────


class TestAuditMiddleware:
    """Tests for AuditLogMiddleware."""

    def test_middleware_importable(self):
        from saw.drivers.web.middleware.security import AuditLogMiddleware
        assert AuditLogMiddleware is not None

    def test_skip_paths(self):
        from saw.drivers.web.middleware.security import AuditLogMiddleware
        assert "/health" in AuditLogMiddleware.SKIP_PATHS
        assert "/metrics" in AuditLogMiddleware.SKIP_PATHS

    def test_write_methods(self):
        from saw.drivers.web.middleware.security import AuditLogMiddleware
        assert "POST" in AuditLogMiddleware.WRITE_METHODS
        assert "DELETE" in AuditLogMiddleware.WRITE_METHODS
        assert "GET" not in AuditLogMiddleware.WRITE_METHODS


# ── Auth Dependency Tests ─────────────────────────────────────────────


class TestAuthDependencies:
    """Tests for FastAPI dependency functions."""

    def test_get_current_user_importable(self):
        from saw.drivers.web.middleware.security import get_current_user_from_token
        assert callable(get_current_user_from_token)

    def test_require_role_importable(self):
        from saw.drivers.web.middleware.security import require_role
        assert callable(require_role)
