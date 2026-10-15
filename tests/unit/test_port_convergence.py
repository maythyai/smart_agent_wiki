"""AC-C-1: Port convergence (F-V-4).

Verifies that vite.config.ts proxy targets have been converged from
8080 to 8000 to match the saw web default port (D-02).
Ground: SPEC-F-V-4, ADR-017 decision 2.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VITE_CONFIG = ROOT / "web" / "vite.config.ts"


@pytest.fixture()
def vite_content() -> str:
    return VITE_CONFIG.read_text(encoding="utf-8")


def test_api_proxy_target_is_8000(vite_content: str) -> None:
    """vite proxy /api target defaults to port 8000 (not 8080).

    v1.33.0 (AUDIT-F-06): target is now env-configurable via
    VITE_API_TARGET, defaulting to http://localhost:8000.
    """
    # Find the /api proxy block — target may be an env expression
    # (process.env.VITE_API_TARGET || 'http://localhost:8000')
    api_match = re.search(r"'/api'[^\n]*\n\s*target:\s*(.+)", vite_content)
    assert api_match is not None, "Could not find /api proxy target in vite.config.ts"
    target_line = api_match.group(1)
    assert "8000" in target_line, f"/api proxy target should contain '8000', got: {target_line}"
    assert "8080" not in target_line, f"/api proxy target should NOT contain '8080', got: {target_line}"


def test_ws_proxy_target_is_8000(vite_content: str) -> None:
    """vite proxy /ws target defaults to port 8000 (not 8080).

    v1.33.0 (AUDIT-F-06): target is now env-configurable via
    VITE_API_TARGET, defaulting to ws://localhost:8000.
    """
    ws_match = re.search(r"'/ws'[^\n]*\n\s*target:\s*(.+)", vite_content)
    assert ws_match is not None, "Could not find /ws proxy target in vite.config.ts"
    target_line = ws_match.group(1)
    assert "8000" in target_line, f"/ws proxy target should contain '8000', got: {target_line}"
    assert "8080" not in target_line, f"/ws proxy target should NOT contain '8080', got: {target_line}"


def test_no_8080_references_remain(vite_content: str) -> None:
    """No remaining references to port 8080 in vite.config.ts."""
    assert "8080" not in vite_content, \
        "vite.config.ts still references port 8080 — port convergence incomplete"


def test_vite_dev_server_port_unchanged(vite_content: str) -> None:
    """vite dev server port remains 5173 (tauri devUrl target)."""
    assert "port: 5173" in vite_content, \
        "vite.config.ts server.port is not 5173"
