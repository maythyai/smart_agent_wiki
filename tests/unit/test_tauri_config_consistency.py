"""AC-V-2: tauri.conf.json configuration consistency (F-V-1).

Verifies the Tauri v2 configuration has no deprecated fields and all
key settings match the expected values for desktop 1.0.
Ground: SPEC-F-V-1 dimension 6, ADR-017.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TAURI_CONF = ROOT / "desktop" / "src-tauri" / "tauri.conf.json"


@pytest.fixture()
def tauri_config() -> dict:
    return json.loads(TAURI_CONF.read_text(encoding="utf-8"))


def test_schema_is_tauri_v2(tauri_config: dict) -> None:
    """$schema points to Tauri v2 config schema."""
    assert tauri_config["$schema"] == "https://schema.tauri.app/config/2"


def test_frontend_dist_points_to_web_dist(tauri_config: dict) -> None:
    """frontendDist resolves to project-root web/dist/."""
    assert tauri_config["build"]["frontendDist"] == "../../web/dist"


def test_dev_url_points_to_vite(tauri_config: dict) -> None:
    """devUrl points to vite dev server on localhost:5173."""
    assert tauri_config["build"]["devUrl"] == "http://localhost:5173"


def test_before_dev_command(tauri_config: dict) -> None:
    """beforeDevCommand starts vite dev server."""
    assert tauri_config["build"]["beforeDevCommand"] == "npm run dev --prefix ../web"


def test_before_build_command(tauri_config: dict) -> None:
    """beforeBuildCommand builds the web frontend."""
    assert tauri_config["build"]["beforeBuildCommand"] == "npm run build --prefix ../web"


def test_bundle_active(tauri_config: dict) -> None:
    """Bundle packaging is enabled."""
    assert tauri_config["bundle"]["active"] is True


def test_bundle_targets_cross_platform(tauri_config: dict) -> None:
    """bundle.targets covers macOS, Windows, and Linux."""
    targets = tauri_config["bundle"]["targets"]
    assert "app" in targets
    assert "dmg" in targets
    assert "deb" in targets
    assert "nsis" in targets


def test_macos_minimum_system_version(tauri_config: dict) -> None:
    """macOS minimumSystemVersion is 10.13."""
    assert tauri_config["bundle"]["macOS"]["minimumSystemVersion"] == "10.13"


def test_macos_entitlements_null(tauri_config: dict) -> None:
    """macOS entitlements is null (unsigned, deferred)."""
    assert tauri_config["bundle"]["macOS"]["entitlements"] is None


def test_windows_webview_install_mode(tauri_config: dict) -> None:
    """Windows WebView2 uses downloadBootstrapper with silent install."""
    wv = tauri_config["bundle"]["windows"]["webviewInstallMode"]
    assert wv["type"] == "downloadBootstrapper"
    assert wv["silent"] is True


def test_windows_digest_algorithm(tauri_config: dict) -> None:
    """Windows digest algorithm is sha256."""
    assert tauri_config["bundle"]["windows"]["digestAlgorithm"] == "sha256"


def test_linux_deb_depends(tauri_config: dict) -> None:
    """Linux deb depends on libwebkit2gtk-4.1-0."""
    depends = tauri_config["bundle"]["linux"]["deb"]["depends"]
    assert "libwebkit2gtk-4.1-0" in depends


def test_no_deprecated_fields(tauri_config: dict) -> None:
    """No deprecated Tauri v1 fields present (upgraders residue)."""
    # Tauri v1 used "tauri" top-level key; v2 uses "build"/"app"/"bundle".
    deprecated_keys = {"tauri", "buildConfig", "tauriFeatures"}
    for key in deprecated_keys:
        assert key not in tauri_config, f"Deprecated field '{key}' found"

    # Tauri v1 used "updater" under bundle; v2 uses plugins.
    assert "updater" not in tauri_config.get("bundle", {})

    # Tauri v1 used "allowlist"; v2 uses capabilities.
    assert "allowlist" not in tauri_config

    # app.security.csp exists (can be null for dev).
    assert "security" in tauri_config["app"]
    assert "csp" in tauri_config["app"]["security"]


def test_plugin_shell_open(tauri_config: dict) -> None:
    """plugins.shell.open is true (allows external links)."""
    assert tauri_config["plugins"]["shell"]["open"] is True


def test_identifier(tauri_config: dict) -> None:
    """Identifier is com.smart-agent.wiki."""
    assert tauri_config["identifier"] == "com.smart-agent.wiki"


def test_product_name(tauri_config: dict) -> None:
    """productName is Smart Agent Wiki."""
    assert tauri_config["productName"] == "Smart Agent Wiki"
