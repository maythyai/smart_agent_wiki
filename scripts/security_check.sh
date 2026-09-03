#!/usr/bin/env bash
# security_check.sh — Bare route detection for SAW Web API (T-F-C-1-1 / AC-SEC-1).
#
# Scans drivers/web/app.py include_router assembly, classifies each router
# as protected (auth_dep / connector_auth_dep) or public, and flags any
# "bare" route — a router with no auth dependency that is not a recognised
# legitimate public endpoint (health, OAuth, HMAC-webhook, auth login).
#
# Usage:
#   bash scripts/security_check.sh [path/to/app.py]
#
# Exit codes:
#   0 — no bare write routes (pass)
#   1 — bare write routes detected (fail)
#   2 — usage / parse error
set -euo pipefail

APP_PY="${1:-src/saw/drivers/web/app.py}"

if [ ! -f "$APP_PY" ]; then
    echo "ERROR: app.py not found at $APP_PY" >&2
    exit 2
fi

python3 - "$APP_PY" <<'PYEOF'
"""Bare route detection — embedded in security_check.sh."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

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

# HTTP methods that constitute "write" operations.
WRITE_METHODS: tuple[str, ...] = ("post", "put", "delete", "patch")


# ── Parsing helpers ─────────────────────────────────────────────────


def split_args(s: str) -> list[str]:
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


def extract_include_router_calls(content: str) -> list[dict[str, Any]]:
    """Extract all app.include_router(...) calls from app.py content.

    Returns a list of dicts with keys: call, line, comment.
    """
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
                    # Extract trailing comment on the same line.
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


def parse_call(call_text: str) -> dict[str, Any]:
    """Parse a single include_router call to extract its components."""
    inner = call_text[len("app.include_router(") : -1]
    parts = split_args(inner)
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


def is_protected(dependencies: str | None) -> bool:
    """Check if a router has auth dependencies (auth_dep or connector_auth_dep)."""
    if dependencies is None:
        return False
    return "auth_dep" in dependencies


def is_legitimate_public(
    router_expr: str | None,
    tags: list[str],
    comment: str,
) -> bool:
    """Check if a public (no auth_dep) router is legitimately public.

    Legitimate public routes are identified by:
    - WebSocket tag
    - Router name pattern (health, oauth, webhook, auth_router)
    - Comment marker (public, HMAC, no JWT, OAuth)
    """
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


def find_router_source_file(
    router_expr: str,
    app_content: str,
    app_dir: Path,
) -> Path | None:
    """Attempt to locate the source file defining a router variable."""
    # Strip function call parens, e.g. get_notion_router() -> get_notion_router
    var_name = re.sub(r"\(\)$", "", router_expr)
    # Look for import statement: "from saw.xxx import yyy as var_name"
    # or "from saw.xxx import var_name"
    patterns = [
        rf"from\s+(\S+)\s+import\s+.*\b{re.escape(var_name)}\b",
        rf"import\s+(\S+)\s+as\s+{re.escape(var_name)}",
    ]
    for pat in patterns:
        m = re.search(pat, app_content)
        if m:
            module_path = m.group(1)
            # Convert saw.xxx.yyy -> saw/xxx/yyy.py
            rel = module_path.replace(".", "/")
            candidate = app_dir / ".." / ".." / ".." / f"{rel}.py"
            candidate = candidate.resolve()
            if candidate.exists():
                return candidate
    return None


def has_write_methods(source_path: Path) -> bool:
    """Check if a router source file contains write HTTP method decorators."""
    try:
        content = source_path.read_text()
    except OSError:
        return False
    for method in WRITE_METHODS:
        if re.search(rf"@router\.{method}\s*\(", content, re.IGNORECASE):
            return True
    return False


# ── Main ────────────────────────────────────────────────────────────


def main(app_path: str) -> int:
    app_file = Path(app_path)
    content = app_file.read_text()
    app_dir = app_file.parent

    calls = extract_include_router_calls(content)
    if not calls:
        print("WARN: no include_router calls found in %s" % app_path)
        return 0

    results: list[dict[str, Any]] = []
    bare_routes: list[dict[str, Any]] = []
    bare_write_routes: list[dict[str, Any]] = []

    for call in calls:
        parsed = parse_call(call["call"])
        parsed["line"] = call["line"]
        parsed["comment"] = call["comment"]
        protected = is_protected(parsed["dependencies"])
        legit = is_legitimate_public(
            parsed["router"], parsed["tags"], call["comment"]
        )
        parsed["protected"] = protected
        parsed["legitimate_public"] = legit

        if not protected and not legit:
            bare_routes.append(parsed)
            # Check for write methods
            src = find_router_source_file(
                parsed["router"] or "", content, app_dir
            )
            if src and has_write_methods(src):
                parsed["has_write"] = True
                bare_write_routes.append(parsed)
            else:
                parsed["has_write"] = False

        results.append(parsed)

    # ── Report ──────────────────────────────────────────────────────
    print("=" * 70)
    print("SAW Security Check — Bare Route Detection (AC-SEC-1)")
    print("=" * 70)
    print(f"Source: {app_path}")
    print(f"Total routers: {len(results)}")
    print(f"Protected (auth_dep):  {sum(1 for r in results if r['protected'])}")
    print(
        f"Legitimate public:     "
        f"{sum(1 for r in results if not r['protected'] and r['legitimate_public'])}"
    )
    print(f"Bare routes:           {len(bare_routes)}")
    print(f"Bare write routes:     {len(bare_write_routes)}")
    print("-" * 70)

    for r in results:
        status = "PROTECTED" if r["protected"] else (
            "PUBLIC" if r["legitimate_public"] else "BARE"
        )
        dep = r["dependencies"] or "—"
        print(
            f"  [{status:9s}] L{r['line']:>3d}  {r['router']:40s}  "
            f"dep={dep}"
        )

    if bare_routes:
        print("-" * 70)
        print("BARE ROUTES (no auth_dep, not recognised as legitimate public):")
        for r in bare_routes:
            write_flag = " [WRITE]" if r.get("has_write") else ""
            print(
                f"  L{r['line']}  {r['router']}{write_flag}  "
                f"comment={r['comment'] or '—'}"
            )

    print("=" * 70)
    if bare_write_routes:
        print("FAIL: %d bare write route(s) detected — missing auth_dep" % len(bare_write_routes))
        return 1
    if bare_routes:
        print("WARN: %d bare route(s) (non-write) — review recommended" % len(bare_routes))
        return 0
    print("PASS: 0 bare write routes")
    return 0


if __name__ == "__main__":
    app_path = sys.argv[1] if len(sys.argv) > 1 else "src/saw/drivers/web/app.py"
    sys.exit(main(app_path))
PYEOF
