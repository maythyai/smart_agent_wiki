"""AC-C-3: CORS expansion (F-V-4).

Verifies that localhost:5173 (vite dev server port) has been added to
the default CORS origins in both web_cmd.py (CLI default) and app.py
(fallback default), enabling desktop dev mode to access saw web.
Ground: SPEC-F-V-4, ADR-017 decision 3.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WEB_CMD = ROOT / "src" / "saw" / "drivers" / "cli" / "commands" / "web_cmd.py"
APP_PY = ROOT / "src" / "saw" / "drivers" / "web" / "app.py"


@pytest.fixture()
def web_cmd_content() -> str:
    return WEB_CMD.read_text(encoding="utf-8")


@pytest.fixture()
def app_py_content() -> str:
    return APP_PY.read_text(encoding="utf-8")


def test_web_cmd_cors_origins_includes_5173(web_cmd_content: str) -> None:
    """web_cmd.py cors_origins default value includes localhost:5173."""
    assert "localhost:5173" in web_cmd_content, \
        "web_cmd.py does not include localhost:5173 in cors_origins default"


def test_web_cmd_cors_origins_default_value(web_cmd_content: str) -> None:
    """web_cmd.py cors_origins default value has all 3 expected origins."""
    match = re.search(
        r'cors_origins.*?typer\.Option\(\s*"([^"]+)"', web_cmd_content, re.DOTALL
    )
    assert match is not None, "Could not extract cors_origins default from web_cmd.py"
    origins = match.group(1)
    assert "localhost:3000" in origins
    assert "127.0.0.1:3000" in origins
    assert "localhost:5173" in origins


def test_app_py_fallback_includes_5173(app_py_content: str) -> None:
    """app.py CORS fallback default includes localhost:5173."""
    assert "localhost:5173" in app_py_content, \
        "app.py does not include localhost:5173 in CORS fallback"


def test_app_py_fallback_origins_list(app_py_content: str) -> None:
    """app.py fallback origins list has all 3 expected entries."""
    # Find the fallback origins list
    match = re.search(
        r'cors_origins\s+or\s*\[([^\]]+)\]', app_py_content
    )
    assert match is not None, "Could not find CORS fallback origins in app.py"
    origins_str = match.group(1)
    assert "localhost:3000" in origins_str
    assert "127.0.0.1:3000" in origins_str
    assert "localhost:5173" in origins_str


def test_app_py_cors_middleware_uses_origins(app_py_content: str) -> None:
    """app.py CORSMiddleware is configured with the origins variable."""
    assert "CORSMiddleware" in app_py_content
    assert "allow_origins" in app_py_content
    assert "allow_credentials" in app_py_content


def test_web_cmd_port_unchanged_at_8000(web_cmd_content: str) -> None:
    """web_cmd.py default port remains 8000 (D-02 convention)."""
    match = re.search(r'port.*?typer\.Option\(\s*(\d+)', web_cmd_content, re.DOTALL)
    assert match is not None, "Could not extract port default from web_cmd.py"
    assert match.group(1) == "8000", \
        f"web_cmd.py default port should be 8000, got: {match.group(1)}"
