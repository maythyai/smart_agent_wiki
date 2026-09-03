"""Tests for observability: logger convergence (T-F-D-1-1).

Covers:
- init_observability is the sole logger init point; no scattered
  basicConfig in src/saw.
- Root logger gets _RequestIdFilter attached after init.
"""
from __future__ import annotations

import logging
from pathlib import Path

# ── T-F-D-1-1: Logger convergence ──────────────────────────────────


def _save_root_logger() -> tuple[list[logging.Handler], int]:
    """Snapshot root logger handlers and level for restoration."""
    root = logging.getLogger()
    return (list(root.handlers), root.level)


def _restore_root_logger(snap: tuple[list[logging.Handler], int]) -> None:
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    for h in snap[0]:
        root.addHandler(h)
    root.setLevel(snap[1])


def test_logger_via_init() -> None:
    """init_observability attaches _RequestIdFilter to root logger handlers."""
    from saw.drivers.web.middleware.observability import (
        _RequestIdFilter,
        init_observability,
    )

    snap = _save_root_logger()
    try:
        # Clear root logger to simulate fresh state.
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

        init_observability(auth_mode="local")

        # Root logger must have at least one handler with _RequestIdFilter.
        assert root.handlers, "root logger should have at least one handler"
        filters_found = [
            f for h in root.handlers for f in h.filters
            if isinstance(f, _RequestIdFilter)
        ]
        assert filters_found, "_RequestIdFilter not attached to any handler"
    finally:
        _restore_root_logger(snap)


def test_logger_via_init_idempotent() -> None:
    """init_observability is safe to call multiple times (no duplicate filters)."""
    from saw.drivers.web.middleware.observability import (
        _RequestIdFilter,
        init_observability,
    )

    snap = _save_root_logger()
    try:
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

        init_observability(auth_mode="local")
        count1 = sum(
            1 for h in root.handlers for f in h.filters
            if isinstance(f, _RequestIdFilter)
        )
        init_observability(auth_mode="local")
        count2 = sum(
            1 for h in root.handlers for f in h.filters
            if isinstance(f, _RequestIdFilter)
        )
        assert count1 == count2 == 1, (
            f"filter count should stay 1, got {count1} then {count2}"
        )
    finally:
        _restore_root_logger(snap)


def test_no_raw_basicconfig() -> None:
    """Lint: no module in src/saw calls logging.basicConfig.

    init_observability is the sole logger initialization point; basicConfig
    bypasses it and would create unconfigured handlers outside the
    request-id filter chain.
    """
    src_dir = Path(__file__).resolve().parents[2] / "src" / "saw"
    assert src_dir.exists(), f"src/saw not found at {src_dir}"

    offenders: list[str] = []
    for py_file in src_dir.rglob("*.py"):
        try:
            text = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        # Skip comments: check for actual calls.
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if "basicConfig" in stripped and "(" in stripped:
                offenders.append(
                    f"{py_file.relative_to(src_dir)}:{i}: {stripped}"
                )

    assert not offenders, (
        "Scattered logging.basicConfig found (must use init_observability):\n"
        + "\n".join(offenders)
    )


# ── T-F-D-3-1: JSON log production default ──────────────────────────

def _has_json_formatter(root: logging.Logger) -> bool:
    """True if any root StreamHandler carries a JsonFormatter."""
    from saw.drivers.web.middleware.observability import JsonFormatter

    return any(
        isinstance(h, logging.StreamHandler)
        and isinstance(h.formatter, JsonFormatter)
        for h in root.handlers
    )


def _fresh_root() -> None:
    """Reset root logger to a single bare StreamHandler (pre-init state)."""
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    root.addHandler(logging.StreamHandler())


def test_json_log_default(monkeypatch) -> None:
    """SPEC-F-D-3: JSON logging is ON by default (production default)."""
    monkeypatch.delenv("SAW_JSON_LOGS", raising=False)
    monkeypatch.delenv("SAW_PRETTY_LOGS", raising=False)
    from saw.drivers.web.middleware.observability import init_observability

    snap = _save_root_logger()
    try:
        _fresh_root()
        init_observability(auth_mode="local")
        assert _has_json_formatter(logging.getLogger()), (
            "JsonFormatter should be attached by default in local mode"
        )
    finally:
        _restore_root_logger(snap)


def test_json_log_pretty_override(monkeypatch) -> None:
    """SAW_PRETTY_LOGS=1 opts back into readable text for local dev."""
    monkeypatch.setenv("SAW_PRETTY_LOGS", "1")
    from saw.drivers.web.middleware.observability import init_observability

    snap = _save_root_logger()
    try:
        _fresh_root()
        init_observability(auth_mode="local")
        assert not _has_json_formatter(logging.getLogger()), (
            "SAW_PRETTY_LOGS=1 should opt out of JSON formatting"
        )
    finally:
        _restore_root_logger(snap)


def test_json_log_explicit_off(monkeypatch) -> None:
    """SAW_JSON_LOGS=0 explicitly disables JSON (backward-compat escape)."""
    monkeypatch.setenv("SAW_JSON_LOGS", "0")
    from saw.drivers.web.middleware.observability import init_observability

    snap = _save_root_logger()
    try:
        _fresh_root()
        init_observability(auth_mode="local")
        assert not _has_json_formatter(logging.getLogger())
    finally:
        _restore_root_logger(snap)


def test_json_log_team_mode(monkeypatch) -> None:
    """Team mode forces JSON regardless of local-dev overrides."""
    monkeypatch.setenv("SAW_PRETTY_LOGS", "1")  # would normally opt out
    from saw.drivers.web.middleware.observability import init_observability

    snap = _save_root_logger()
    try:
        _fresh_root()
        init_observability(auth_mode="team")
        assert _has_json_formatter(logging.getLogger()), (
            "team mode must force JSON even with SAW_PRETTY_LOGS=1"
        )
    finally:
        _restore_root_logger(snap)


# ── T-F-D-3-1: /health/ready reflects engine readiness (AC-OBS-2) ───

async def test_health_ready_reflects_engine_down(monkeypatch) -> None:
    """AC-OBS-2: missing engines → /health/ready returns 503 not_ready."""
    from types import SimpleNamespace

    from saw.drivers.web.health import readiness_check

    # Isolate the engine check: DB/Redis are mocked healthy so engines are
    # the sole deciding factor.
    monkeypatch.setattr(
        "saw.drivers.web.health.check_database",
        lambda: {"status": "healthy"},
    )
    monkeypatch.setattr(
        "saw.drivers.web.health.check_redis",
        lambda: {"status": "skipped", "reason": "not configured"},
    )

    state = SimpleNamespace(query=None, collaborate=None, write_queue=None)
    request = SimpleNamespace(app=SimpleNamespace(state=state))
    response = SimpleNamespace(status_code=200)

    result = await readiness_check(request, response)

    assert response.status_code == 503
    assert result["status"] == "not_ready"
    assert result["checks"]["engines"]["status"] == "unhealthy"


async def test_health_ready_passes_when_engines_ok(monkeypatch) -> None:
    """AC-OBS-2: all engines present + deps healthy → 200 ready."""
    from types import SimpleNamespace

    from saw.drivers.web.health import readiness_check

    monkeypatch.setattr(
        "saw.drivers.web.health.check_database",
        lambda: {"status": "healthy"},
    )
    monkeypatch.setattr(
        "saw.drivers.web.health.check_redis",
        lambda: {"status": "skipped", "reason": "not configured"},
    )

    state = SimpleNamespace(
        query=object(), collaborate=object(), write_queue=object()
    )
    request = SimpleNamespace(app=SimpleNamespace(state=state))
    response = SimpleNamespace(status_code=200)

    result = await readiness_check(request, response)

    assert response.status_code == 200
    assert result["status"] == "ready"
    assert result["checks"]["engines"]["status"] == "healthy"
