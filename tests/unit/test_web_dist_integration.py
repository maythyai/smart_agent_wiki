"""AC-W-1: web/dist prod integration (F-V-2).

Verifies that the web frontend build output (web/dist/) exists and is
correctly referenced by tauri.conf.json's frontendDist path, and that
@tauri-apps/api is integrated in the web package.
Ground: SPEC-F-V-2, ADR-017.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WEB_DIST = ROOT / "web" / "dist"
TAURI_CONF = ROOT / "desktop" / "src-tauri" / "tauri.conf.json"
WEB_PKG = ROOT / "web" / "package.json"


@pytest.fixture()
def tauri_config() -> dict:
    return json.loads(TAURI_CONF.read_text(encoding="utf-8"))


def test_web_dist_index_html_exists() -> None:
    """web/dist/index.html exists and is non-empty."""
    index_html = WEB_DIST / "index.html"
    assert index_html.exists(), "web/dist/index.html not found"
    content = index_html.read_text(encoding="utf-8")
    assert len(content) > 0, "web/dist/index.html is empty"


def test_web_dist_index_html_references_assets() -> None:
    """web/dist/index.html references compiled assets (JS + CSS)."""
    content = (WEB_DIST / "index.html").read_text(encoding="utf-8")
    # Vite produces hashed asset filenames like index-HASH.js
    assert re.search(r'/assets/index-[A-Za-z0-9_-]+\.js', content), \
        "index.html does not reference compiled JS asset"
    assert re.search(r'/assets/index-[A-Za-z0-9_-]+\.css', content), \
        "index.html does not reference compiled CSS asset"


def test_web_dist_assets_dir_exists() -> None:
    """web/dist/assets/ directory exists with compiled files."""
    assets_dir = WEB_DIST / "assets"
    assert assets_dir.is_dir(), "web/dist/assets/ directory not found"
    asset_files = list(assets_dir.iterdir())
    assert len(asset_files) >= 2, "assets/ should contain at least JS + CSS"


def test_frontend_dist_resolves_correctly(tauri_config: dict) -> None:
    """tauri.conf.json frontendDist = ../../web/dist (relative to src-tauri/)."""
    frontend_dist = tauri_config["build"]["frontendDist"]
    assert frontend_dist == "../../web/dist"
    # Resolve relative to desktop/src-tauri/ → project root web/dist/
    src_tauri = ROOT / "desktop" / "src-tauri"
    resolved = (src_tauri / frontend_dist).resolve()
    assert resolved == WEB_DIST.resolve(), \
        f"frontendDist resolves to {resolved}, expected {WEB_DIST.resolve()}"


def test_before_build_command_triggers_web_build(tauri_config: dict) -> None:
    """beforeBuildCommand triggers npm run build for the web frontend."""
    assert tauri_config["build"]["beforeBuildCommand"] == "npm run build --prefix ../web"


def test_tauri_apps_api_integrated() -> None:
    """web/package.json includes @tauri-apps/api dependency."""
    pkg = json.loads(WEB_PKG.read_text(encoding="utf-8"))
    deps = pkg.get("dependencies", {})
    assert "@tauri-apps/api" in deps, "@tauri-apps/api not in web dependencies"
    # Version should be ^2.0.0 (Tauri v2)
    version = deps["@tauri-apps/api"]
    assert version.startswith("^2.") or version.startswith("2."), \
        f"@tauri-apps/api version {version} is not v2"
