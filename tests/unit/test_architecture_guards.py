"""Architecture guard tests (M-21).

Enforces the hexagonal layering contract + file-size limits so the boundaries
don't erode again. These are architecture-level (not behavior) tests:

* domain/ must not import inward layers (engines/adapters/drivers/api/
  connectors/db) — pure-Python core.
* adapters/ (infrastructure) must not import entry points or engines
  (drivers/api/engines).
* every saw.* subpackage imports without circular errors.
* no src/saw Python file exceeds the size limit (god-file guard; currently 750 —
  lowered as M-4 splits the big files).
"""
from __future__ import annotations

import ast
import importlib
import pkgutil
from pathlib import Path

import pytest

import saw

SRC = Path(saw.__file__).resolve().parent  # .../src/saw

# layer path -> import roots it must NOT depend on (inward dependencies).
_FORBIDDEN = {
    "domain": (
        "saw.engines", "saw.adapters", "saw.drivers", "saw.api",
        "saw.connectors", "saw.db",
    ),
    "adapters": ("saw.drivers", "saw.api", "saw.engines"),
}

SIZE_LIMIT = 750  # god-file threshold (lines); lower as M-4 splits big files.


def _imported_saw_roots(source: str) -> set[str]:
    """Return the set of ``saw.*`` import roots referenced in *source*."""
    roots: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return roots
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.startswith("saw."):
                    roots.add(n.name.split(".")[1])  # saw.engines.foo -> engines
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("saw."):
                roots.add(node.module.split(".")[1])
    # map single-segment "saw" -> "" (the package itself, ignored)
    roots.discard("saw")
    return {f"saw.{r}" for r in roots}


def _layer_files(layer: str) -> list[Path]:
    base = SRC / layer
    if not base.is_dir():
        return []
    return [p for p in base.rglob("*.py") if p.name != "__init__.py" and "__pycache__" not in str(p)]


def _runtime_upward_deps(layer: str, forbidden: tuple[str, ...]) -> set[str]:
    """Import every module under *layer* and return inward deps it pulled in.

    Uses a sys.modules snapshot so TYPE_CHECKING-only imports (which never
    execute) are correctly ignored — only real runtime dependencies count.
    """
    import sys

    before = set(sys.modules)
    base_pkg = f"saw.{layer}"
    importlib.import_module(base_pkg)
    layer_path = getattr(importlib.import_module(base_pkg), "__path__", None)
    if layer_path:
        for m in pkgutil.walk_packages(layer_path, f"{base_pkg}."):
            try:
                importlib.import_module(m.name)
            except Exception:
                pass
    after = set(sys.modules) - before
    pulled = set()
    for mod in after:
        if mod.startswith("saw."):
            root = "saw." + mod.split(".")[1]
            if root in forbidden:
                pulled.add(root)
    return pulled


# ── layering (runtime: TYPE_CHECKING imports don't count) ──────────


def test_domain_layer_no_upward_imports():
    """domain/ must not import inward layers at runtime (engines/adapters/...)."""
    bad = _runtime_upward_deps("domain", _FORBIDDEN["domain"])
    assert not bad, f"domain pulled inward layers at runtime: {sorted(bad)}"


def test_adapters_layer_no_upward_imports():
    """adapters/ (infrastructure) must not reach entry points or engines."""
    bad = _runtime_upward_deps("adapters", _FORBIDDEN["adapters"])
    assert not bad, f"adapters pulled inward layers at runtime: {sorted(bad)}"


# ── circular imports ────────────────────────────────────────────────


def test_all_saw_modules_import_without_circular_errors():
    """Import every saw.* subpackage — a circular import raises ImportError."""
    errors: list[tuple[str, str]] = []
    for m in pkgutil.walk_packages(saw.__path__, "saw."):
        try:
            importlib.import_module(m.name)
        except Exception as e:  # noqa: BLE001
            errors.append((m.name, f"{type(e).__name__}: {e}"[:120]))
    assert not errors, "circular/import errors:\n  " + "\n  ".join(
        f"{n}: {e}" for n, e in errors
    )


# ── god-file guard ──────────────────────────────────────────────────


def test_no_src_file_exceeds_size_limit():
    """No src/saw Python file may exceed SIZE_LIMIT lines (god-file guard)."""
    over = []
    for p in SRC.rglob("*.py"):
        if "__pycache__" in str(p):
            continue
        n = len(p.read_text(encoding="utf-8").splitlines())
        if n > SIZE_LIMIT:
            over.append((p.relative_to(SRC.parent), n))
    assert not over, (
        f"files >{SIZE_LIMIT} lines (split per M-4):\n  "
        + "\n  ".join(f"{p}: {n}" for p, n in sorted(over, key=lambda x: -x[1]))
    )
