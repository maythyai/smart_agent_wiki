"""AC-C-2: Prod backend connection (F-V-4).

Verifies that the frontend prod-mode connection configuration (VITE_API_BASE_URL
and VITE_WS_URL) is correctly wired in the existing code, enabling desktop
prod mode to connect to an external saw web backend.
Ground: SPEC-F-V-4, ADR-017 decision 1.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
API_TS = ROOT / "web" / "src" / "lib" / "api.ts"
WS_HOOK_TS = ROOT / "web" / "src" / "hooks" / "useWebSocket.ts"


@pytest.fixture()
def api_content() -> str:
    return API_TS.read_text(encoding="utf-8")


@pytest.fixture()
def ws_content() -> str:
    return WS_HOOK_TS.read_text(encoding="utf-8")


def test_api_base_uses_env_var(api_content: str) -> None:
    """api.ts reads VITE_API_BASE_URL from env (fallback to empty = relative)."""
    assert "VITE_API_BASE_URL" in api_content, \
        "api.ts does not reference VITE_API_BASE_URL"


def test_api_base_fallback_is_empty(api_content: str) -> None:
    """api.ts API_BASE fallback is empty string (dev proxy relative path)."""
    match = re.search(
        r"VITE_API_BASE_URL\s*\|\|\s*['\"]([^'\"]*)['\"]", api_content
    )
    assert match is not None, \
        "Could not find VITE_API_BASE_URL fallback in api.ts"
    assert match.group(1) == "", \
        f"VITE_API_BASE_URL fallback should be empty string, got: '{match.group(1)}'"


def test_ws_url_uses_env_var(ws_content: str) -> None:
    """useWebSocket.ts reads VITE_WS_URL from env."""
    assert "VITE_WS_URL" in ws_content, \
        "useWebSocket.ts does not reference VITE_WS_URL"


def test_ws_url_fallback_uses_window_location(ws_content: str) -> None:
    """useWebSocket.ts WS_URL fallback uses window.location.host (dev proxy)."""
    assert "window.location.host" in ws_content, \
        "useWebSocket.ts WS_URL fallback does not use window.location.host"
    assert "/ws" in ws_content, \
        "useWebSocket.ts WS_URL fallback does not include /ws path"


def test_ws_url_fallback_protocol_aware(ws_content: str) -> None:
    """useWebSocket.ts WS_URL fallback handles wss/ws protocol switching."""
    assert "wss:" in ws_content, "useWebSocket.ts does not handle wss protocol"
    assert "ws:" in ws_content, "useWebSocket.ts does not handle ws protocol"
