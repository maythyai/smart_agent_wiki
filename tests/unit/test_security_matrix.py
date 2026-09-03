"""Tests for security matrix and bare route detection (AC-SEC-1).

Covers SPEC-F-C-1 / T-F-C-1-1:
- AC-SEC-1: 0 unprotected (bare) write routes in the FastAPI assembly.
- Protected routes have auth_dep / connector_auth_dep attached.

The parsing logic is self-contained so tests can run without importing
the bash script. A subprocess test validates the script end-to-end.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

import pytest

# ── Paths ───────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).resolve().parents[2]
_APP_PY = _REPO_ROOT / "src" / "saw" / "drivers" / "web" / "app.py"
_SCRIPT = _REPO_ROOT / "scripts" / "security_check.sh"

# ── Constants ───────────────────────────────────────────────────────

# Router variable names that are legitimately public (no auth_dep needed).
LEGIT_PUBLIC_NAME_PATTERNS: tuple[str, ...] = (
    "health",
    "oauth",
    "webhook",
    "auth_router",  # login/register/refresh/logout
)

# Comment markers signalling a legitimate public route.
LEGIT_PUBLIC_COMMENT_MARKERS: tuple[str, ...] = (
    "public",
    "hmac",
    "no jwt",
    "oauth",
)


# ── Parsing helpers ─────────────────────────────────────────────────


def _split_args(s: str) -> list[str]:
    """Split function arguments by commas, respecting nested brackets."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for c in s:
        if c in "([{":
            depth += 1
            current.append(c)
        elif c in ")]}":
            depth -= 1
            current.append(c)
        elif c == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(c)
    if current:
        parts.append("".join(current))
    return parts


def _extract_include_router_calls(content: str) -> list[dict[str, Any]]:
    """Extract all app.include_router(...) calls from app.py content."""
    calls: list[dict[str, Any]] = []
    for m in re.finditer(r"app\.include_router\(", content):
        start = m.start()
        paren_pos = m.end() - 1  # index of '('
        depth = 0
        i = paren_pos
        while i < len(content):
            ch = content[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    call_text = content[start : i + 1]
                    line_no = content[:start].count("\n") + 1
                    rest = content[i + 1 :]
                    eol = rest.find("\n")
                    line_rest = rest if eol == -1 else rest[:eol]
                    comment = ""
                    if "#" in line_rest:
                        comment = line_rest[line_rest.find("#") :].strip()
                    calls.append(
                        {"call": call_text, "line": line_no, "comment": comment}
                    )
                    break
            i += 1
    return calls


def _parse_call(call_text: str) -> dict[str, Any]:
    """Parse a single include_router call to extract its components."""
    inner = call_text[len("app.include_router(") : -1]
    parts = _split_args(inner)
    router_expr: str | None = None
    prefix: str | None = None
    tags: list[str] = []
    dependencies: str | None = None
    for part in parts:
        p = part.strip()
        if p.startswith("prefix="):
            val = p[len("prefix=") :].strip()
            prefix = val.strip('"').strip("'")
        elif p.startswith("tags="):
            tags = re.findall(r'"([^"]*)"', p)
        elif p.startswith("dependencies="):
            dependencies = p[len("dependencies=") :].strip()
        elif router_expr is None:
            router_expr = p
    return {
        "router": router_expr,
        "prefix": prefix,
        "tags": tags,
        "dependencies": dependencies,
    }


def _is_protected(dependencies: str | None) -> bool:
    """Check if a router has auth dependencies."""
    if dependencies is None:
        return False
    return "auth_dep" in dependencies


def _is_legitimate_public(
    router_expr: str | None,
    tags: list[str],
    comment: str,
) -> bool:
    """Check if a public (no auth_dep) router is legitimately public."""
    if "websocket" in tags:
        return True
    router_lower = (router_expr or "").lower()
    for pattern in LEGIT_PUBLIC_NAME_PATTERNS:
        if pattern in router_lower:
            return True
    comment_lower = (comment or "").lower()
    for marker in LEGIT_PUBLIC_COMMENT_MARKERS:
        if marker in comment_lower:
            return True
    return False


def _parse_all_routers() -> list[dict[str, Any]]:
    """Parse app.py and return a list of router info dicts."""
    content = _APP_PY.read_text()
    calls = _extract_include_router_calls(content)
    results: list[dict[str, Any]] = []
    for call in calls:
        parsed = _parse_call(call["call"])
        parsed["line"] = call["line"]
        parsed["comment"] = call["comment"]
        parsed["protected"] = _is_protected(parsed["dependencies"])
        parsed["legitimate_public"] = _is_legitimate_public(
            parsed["router"], parsed["tags"], call["comment"]
        )
        results.append(parsed)
    return results


# ── Tests: AC-SEC-1 — 0 bare write routes ──────────────────────────


class TestNoUnprotectedWriteRoutes:
    """AC-SEC-1: no unprotected write routes in the FastAPI assembly."""

    def test_no_unprotected_write_routes(self) -> None:
        """Every router must be protected or a recognised legitimate public."""
        routers = _parse_all_routers()
        bare = [
            r
            for r in routers
            if not r["protected"] and not r["legitimate_public"]
        ]
        assert bare == [], (
            f"Found {len(bare)} bare (unprotected, non-public) routers: "
            f"{[r['router'] for r in bare]}"
        )

    def test_security_check_script_exit_zero(self) -> None:
        """security_check.sh exits 0 — no bare write routes."""
        assert _SCRIPT.exists(), f"Script not found: {_SCRIPT}"
        result = subprocess.run(
            ["bash", str(_SCRIPT), str(_APP_PY)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0, (
            f"security_check.sh exited {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        assert "PASS" in result.stdout
        assert "0 bare write routes" in result.stdout


# ── Tests: protected routes have auth_dep ──────────────────────────


class TestAuthDepAttached:
    """Protected routes have auth_dep or connector_auth_dep attached."""

    def test_all_non_public_routers_have_auth_dep(self) -> None:
        """Every non-legitimate-public router must carry auth_dep."""
        routers = _parse_all_routers()
        for r in routers:
            if not r["protected"]:
                assert r["legitimate_public"], (
                    f"Router {r['router']} (line {r['line']}) has no auth_dep "
                    f"and is not a recognised legitimate public route"
                )

    @pytest.mark.parametrize(
        "router_name",
        [
            "graph_router",
            "pages_router",
            "search_router",
            "import_router",
            "capture_router",
            "templates_router",
            "entity_types_router",
            "onboarding_router",
            "timeline_router",
            "connector_settings_router",
            "dashboard_stats_router",
            "feeds_router",
            "sync_router",
            "integrations_router",
            "govern_router",
            "impact_router",
            "qil_router",
            "collaborate_api_router",
        ],
    )
    def test_known_write_router_is_protected(self, router_name: str) -> None:
        """Spot-check: known write/sensitive routers have auth_dep."""
        routers = _parse_all_routers()
        by_router: dict[str, dict[str, Any]] = {
            r["router"]: r for r in routers if r["router"] is not None
        }
        assert router_name in by_router, f"Router {router_name} not found in app.py"
        r = by_router[router_name]
        assert r["protected"], (
            f"Router {router_name} (line {r['line']}) is NOT protected "
            f"— missing auth_dep"
        )

    def test_connector_settings_uses_connector_auth_dep(self) -> None:
        """Connector settings require admin/editor role (connector_auth_dep)."""
        routers = _parse_all_routers()
        by_router: dict[str, dict[str, Any]] = {
            r["router"]: r for r in routers if r["router"] is not None
        }
        r = by_router["connector_settings_router"]
        assert r["dependencies"] == "connector_auth_dep"

    def test_public_routes_are_not_protected(self) -> None:
        """Legitimate public routes (health, oauth, webhook, auth) have no auth_dep."""
        routers = _parse_all_routers()
        public_routers = [r for r in routers if r["legitimate_public"]]
        assert len(public_routers) >= 5, (
            f"Expected at least 5 legitimate public routes, "
            f"got {len(public_routers)}"
        )
        for r in public_routers:
            assert not r["protected"], (
                f"Router {r['router']} (line {r['line']}) is marked as "
                f"legitimate public but also has auth_dep — inconsistent"
            )
