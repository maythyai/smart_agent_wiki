"""AC-W-2: web dev integration (F-V-2).

Verifies that the tauri dev mode configuration correctly points to the
vite dev server on localhost:5173 and that beforeDevCommand starts it.
Ground: SPEC-F-V-2, ADR-017.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TAURI_CONF = ROOT / "desktop" / "src-tauri" / "tauri.conf.json"
VITE_CONFIG = ROOT / "web" / "vite.config.ts"


@pytest.fixture()
def tauri_config() -> dict:
    return json.loads(TAURI_CONF.read_text(encoding="utf-8"))


def test_dev_url_points_to_vite(tauri_config: dict) -> None:
    """tauri.conf.json devUrl = http://localhost:5173 (vite dev server)."""
    assert tauri_config["build"]["devUrl"] == "http://localhost:5173"


def test_before_dev_command_starts_vite(tauri_config: dict) -> None:
    """beforeDevCommand = npm run dev --prefix ../web (starts vite)."""
    assert tauri_config["build"]["beforeDevCommand"] == "npm run dev --prefix ../web"


def test_vite_config_port_matches_dev_url() -> None:
    """vite.config.ts server.port matches tauri devUrl port (5173)."""
    content = VITE_CONFIG.read_text(encoding="utf-8")
    assert "port: 5173" in content, "vite.config.ts server.port is not 5173"


def test_vite_config_has_proxy(tauri_config: dict) -> None:
    """vite.config.ts has proxy configuration for /api and /ws."""
    content = VITE_CONFIG.read_text(encoding="utf-8")
    assert "'/api'" in content or '"/api"' in content, \
        "vite.config.ts does not configure /api proxy"
    assert "'/ws'" in content or '"/ws"' in content, \
        "vite.config.ts does not configure /ws proxy"
