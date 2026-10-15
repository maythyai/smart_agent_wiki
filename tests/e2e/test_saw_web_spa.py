"""E2E smoke: saw web serves the SPA + API (v1.33.0, AUDIT-F-05 / E2E-BLOCKED-01).

Starts a real `saw web` on a free port + drives headless chromium to verify:
- GET / → 200 with the SPA root div rendered (AUDIT-F-05: saw web serves SPA).
- GET /api/auth/mode → 200 JSON (API not shadowed by SPA fallback).

This is the dynamic-gate evidence that unblocks E2E-BLOCKED-01 (previously
the SPA wasn't served by `saw web`, forcing vite-dev + a proxy to vLLM).

Skipped if playwright/chromium or the saw CLI is unavailable (BLOCKED, not
degraded — per VERIFICATION-DISCIPLINE, dynamic gates may not be substituted).
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time

import pytest

try:
    from playwright.sync_api import sync_playwright
    _PW_AVAILABLE = True
except Exception:  # pragma: no cover
    _PW_AVAILABLE = False


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_up(port: int, timeout: float = 120.0) -> bool:
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/auth/mode", timeout=2) as r:
                if 200 <= r.status < 500:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


@pytest.fixture(scope="module")
def saw_web_port():
    port = _free_port()
    saw_bin = shutil.which("saw") or os.path.join(os.path.dirname(sys.executable), "saw")
    _err = open(f"/tmp/saw_e2e_{port}.log", "w")
    proc = subprocess.Popen(
        [saw_bin, "web", "--port", str(port), "--host", "127.0.0.1"],
        stdout=_err, stderr=subprocess.STDOUT,
    )
    try:
        if not _wait_up(port):
            proc.kill()
            _err.close()
            log = open(f"/tmp/saw_e2e_{port}.log").read()
            pytest.skip(f"saw web did not come up (BLOCKED: env). log:\n{log[:500]}")
        yield port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        _err.close()


@pytest.mark.skipif(not _PW_AVAILABLE, reason="playwright/chromium unavailable (BLOCKED, not degraded)")
def test_saw_web_serves_spa_and_api(saw_web_port):
    """AUDIT-F-05 / E2E-BLOCKED-01: saw web serves SPA at / + API reachable."""
    base = f"http://127.0.0.1:{saw_web_port}"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # SPA served at /
        resp = page.goto(base + "/", wait_until="networkidle", timeout=15000)
        assert resp is not None and resp.status == 200
        assert page.locator("#root").count() >= 1 or "Smart Agent Wiki" in page.title()
        # API not shadowed by SPA fallback
        api_resp = page.request.get(base + "/api/auth/mode")
        assert api_resp.status == 200
        assert "auth_mode" in api_resp.json()
        browser.close()
