"""T-F-C-4-1: URL guard coverage + SSRF blocking regression tests.

Verifies assert_safe_url blocks internal/loopback/cloud-metadata/non-http
and that every external-URL entry point (ingest url, feed fetch, outbound
webhook) routes through the guard. Ground: src/saw/adapters/url_guard.py;
call sites per CMS §M08 (HI-12).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from saw.adapters.url_guard import SsrfError, assert_safe_url

SRC = Path(__file__).resolve().parents[1] / "src" / "saw"


# --- blocking behavior ---

@pytest.mark.parametrize("url", [
    "http://127.0.0.1",
    "http://localhost",
    "http://[::1]",
    "http://10.0.0.1",
    "http://192.168.1.1",
    "http://172.16.0.1",
    "http://169.254.169.254",   # AWS IMDS
    "http://0.0.0.0",
])
def test_internal_and_metadata_blocked(url: str) -> None:
    with pytest.raises(SsrfError):
        assert_safe_url(url)


@pytest.mark.parametrize("url", [
    "ftp://example.com",
    "file:///etc/passwd",
    "gopher://example.com",
    "javascript:alert(1)",
])
def test_non_http_scheme_blocked(url: str) -> None:
    with pytest.raises(SsrfError):
        assert_safe_url(url)


def test_empty_and_hostless_blocked() -> None:
    with pytest.raises(SsrfError):
        assert_safe_url("")
    with pytest.raises(SsrfError):
        assert_safe_url("http:///path")


def test_public_ip_literal_passes() -> None:
    # 1.1.1.1 is a public anycast IP; bare-IP path skips DNS so no network.
    assert_safe_url("https://1.1.1.1")  # no raise


# --- coverage of external-URL entry points ---

EXPECTED_CALL_SITES = {
    "adapters/parsers/html_parser.py",      # ingest url extractor
    "engines/ingest/feed_manager.py",        # RSS feed + entry-link fetch
    "api/webhooks.py",                      # outbound webhook delivery
}


def test_guard_referenced_at_all_external_url_entry_points() -> None:
    """Every external-URL entry point must route through assert_safe_url."""
    referenced: set[str] = set()
    for py in SRC.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        if "assert_safe_url" in text and "def assert_safe_url" not in text:
            referenced.add(str(py.relative_to(SRC)).replace("\\", "/"))
    missing = EXPECTED_CALL_SITES - referenced
    assert not missing, f"entry points missing url_guard: {missing}"
