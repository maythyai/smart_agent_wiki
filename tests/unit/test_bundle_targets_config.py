"""AC-B-2: bundle.targets configuration (F-V-3).

Verifies that tauri.conf.json bundle.targets includes macOS targets
(app + dmg) as declared cross-platform goals.
Ground: SPEC-F-V-3, ADR-017.
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


def test_bundle_targets_contains_app(tauri_config: dict) -> None:
    """bundle.targets includes 'app' (macOS .app bundle)."""
    targets = tauri_config["bundle"]["targets"]
    assert "app" in targets, f"'app' not in bundle.targets: {targets}"


def test_bundle_targets_contains_dmg(tauri_config: dict) -> None:
    """bundle.targets includes 'dmg' (macOS disk image)."""
    targets = tauri_config["bundle"]["targets"]
    assert "dmg" in targets, f"'dmg' not in bundle.targets: {targets}"


def test_bundle_targets_contains_deb(tauri_config: dict) -> None:
    """bundle.targets includes 'deb' (Linux Debian package)."""
    targets = tauri_config["bundle"]["targets"]
    assert "deb" in targets, f"'deb' not in bundle.targets: {targets}"


def test_bundle_targets_count(tauri_config: dict) -> None:
    """bundle.targets has at least 5 targets (cross-platform coverage)."""
    targets = tauri_config["bundle"]["targets"]
    assert len(targets) >= 5, f"Expected >=5 bundle targets, got {len(targets)}: {targets}"
