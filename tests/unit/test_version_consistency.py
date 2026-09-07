"""AC-V-1: Version consistency across desktop stack (F-V-1).

Ensures all 4 version-bearing files are aligned at 1.0.0 after the
desktop 1.0 bump. Ground: SPEC-F-V-1, ADR-017.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

DESKTOP_PKG = ROOT / "desktop" / "package.json"
TAURI_CONF = ROOT / "desktop" / "src-tauri" / "tauri.conf.json"
CARGO_TOML = ROOT / "desktop" / "src-tauri" / "Cargo.toml"
WEB_PKG = ROOT / "web" / "package.json"

EXPECTED_VERSION = "1.0.0"


def _extract_pkg_json_version(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["version"]


def _extract_cargo_version(path: Path) -> str:
    match = re.search(r'^version\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.MULTILINE)
    assert match is not None, f"version field not found in {path}"
    return match.group(1)


def test_desktop_package_json_version() -> None:
    """desktop/package.json version == 1.0.0."""
    assert _extract_pkg_json_version(DESKTOP_PKG) == EXPECTED_VERSION


def test_tauri_conf_json_version() -> None:
    """desktop/src-tauri/tauri.conf.json version == 1.0.0."""
    assert _extract_pkg_json_version(TAURI_CONF) == EXPECTED_VERSION


def test_cargo_toml_version() -> None:
    """desktop/src-tauri/Cargo.toml version == 1.0.0."""
    assert _extract_cargo_version(CARGO_TOML) == EXPECTED_VERSION


def test_web_package_json_version() -> None:
    """web/package.json version == 1.0.0."""
    assert _extract_pkg_json_version(WEB_PKG) == EXPECTED_VERSION


def test_all_versions_aligned() -> None:
    """All 4 version-bearing files report the same version (1.0.0)."""
    versions = {
        "desktop/package.json": _extract_pkg_json_version(DESKTOP_PKG),
        "tauri.conf.json": _extract_pkg_json_version(TAURI_CONF),
        "Cargo.toml": _extract_cargo_version(CARGO_TOML),
        "web/package.json": _extract_pkg_json_version(WEB_PKG),
    }
    unique = set(versions.values())
    assert len(unique) == 1, f"Version mismatch: {versions}"
    assert unique.pop() == EXPECTED_VERSION
