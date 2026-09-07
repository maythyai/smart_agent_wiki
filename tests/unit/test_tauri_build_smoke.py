"""AC-B-1: tauri build smoke test (F-V-3).

Runs `tauri build` and verifies the bundle output directory contains at
least one native package. Skipped when cargo/tauri CLI is not available.
Ground: SPEC-F-V-3, ADR-017.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DESKTOP_DIR = ROOT / "desktop"
BUNDLE_DIR = DESKTOP_DIR / "src-tauri" / "target" / "release" / "bundle"

# Skip the entire module if cargo is not installed — tauri build requires
# the Rust toolchain. The config-level tests (test_bundle_targets_config.py)
# run unconditionally.
_HAS_CARGO = shutil.which("cargo") is not None
_HAS_NPM = shutil.which("npm") is not None

pytestmark = pytest.mark.skipif(
    not _HAS_CARGO or not _HAS_NPM,
    reason="cargo or npm not installed — tauri build requires Rust + Node",
)


def test_tauri_build_succeeds() -> None:
    """`tauri build` exits with code 0."""
    # Install tauri CLI if not already present
    tauri_bin = DESKTOP_DIR / "node_modules" / ".bin" / "tauri"
    if not tauri_bin.exists():
        subprocess.run(
            ["npm", "install"],
            cwd=str(DESKTOP_DIR),
            check=True,
            capture_output=True,
            timeout=120,
        )

    result = subprocess.run(
        ["npm", "run", "tauri:build"],
        cwd=str(DESKTOP_DIR),
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, (
        f"tauri build failed with exit code {result.returncode}\n"
        f"stdout: {result.stdout[-2000:]}\n"
        f"stderr: {result.stderr[-2000:]}"
    )


def test_bundle_directory_has_native_packages() -> None:
    """target/release/bundle/ contains at least one native package."""
    if not BUNDLE_DIR.exists():
        # If the build test ran, bundle should exist. If it was skipped
        # (e.g. running this test standalone), try building first.
        test_tauri_build_succeeds()

    assert BUNDLE_DIR.exists(), f"Bundle directory not found: {BUNDLE_DIR}"
    # Look for any package files (.app, .dmg, .deb, .rpm, .msi, .nsis, .AppImage)
    package_extensions = {".app", ".dmg", ".deb", ".rpm", ".msi", ".AppImage"}
    found = []
    for item in BUNDLE_DIR.rglob("*"):
        if item.is_file() and item.suffix in package_extensions:
            found.append(item)
    assert len(found) >= 1, (
        f"No native packages found in {BUNDLE_DIR}. "
        f"Contents: {list(BUNDLE_DIR.rglob('*'))[:20]}"
    )
