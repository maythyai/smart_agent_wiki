"""T-F-B-1-1: claim_diff.sh — actual counts + stale-claim detection.

Tests the script with fixture docs + a synthetic entry-points.jsonl so the
detection logic is deterministic (independent of repo doc state). AC-ALIGN-1.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "claim_diff.sh"
PY = sys.executable


def _run(ep: Path, docs: list[Path]) -> tuple[int, str]:
    args = ["/bin/bash", str(SCRIPT), str(ep), *(str(d) for d in docs)]
    r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def _make_ep(tmp_path: Path, mcp: int, cli: int, web: int) -> Path:
    lines = []
    lines += [f'{{"kind":"mcp","id":"mcp:{i}"}}' for i in range(mcp)]
    lines += [f'{{"kind":"cli","id":"cli:{i}"}}' for i in range(cli)]
    lines += [f'{{"kind":"web","id":"web:{i}"}}' for i in range(web)]
    ep = tmp_path / "entry-points.jsonl"
    ep.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ep


def test_actual_counts(tmp_path: Path) -> None:
    ep = _make_ep(tmp_path, mcp=61, cli=37, web=117)
    doc = tmp_path / "README.md"
    doc.write_text("# Project\nNo claims here.\n", encoding="utf-8")
    code, out = _run(ep, [doc])
    assert code == 0
    assert "mcp tools:  61" in out
    assert "cli cmds:   37" in out
    assert "web routes: 117" in out
    assert "clean" in out


def test_detects_stale_claim(tmp_path: Path) -> None:
    ep = _make_ep(tmp_path, mcp=61, cli=37, web=117)
    doc = tmp_path / "deep_audit.md"
    doc.write_text(
        "README 宣称的 24+ MCP 工具实际只有 6 个、6 个 Agent 的 execute() 为空实现\n",
        encoding="utf-8",
    )
    code, out = _run(ep, [doc])
    assert code == 1
    assert "STALE" in out
    assert "execute() 为空实现" in out


def test_historical_snapshot_annotation_suppresses(tmp_path: Path) -> None:
    """Lines marked 历史快照 / 不作依据 are not flagged (F-B-3 contract)."""
    ep = _make_ep(tmp_path, mcp=61, cli=37, web=117)
    doc = tmp_path / "deep_audit.md"
    doc.write_text(
        "> 历史快照 2026-06-23，不作依据：README 宣称的 24+ MCP 工具实际只有 6 个\n",
        encoding="utf-8",
    )
    code, out = _run(ep, [doc])
    assert code == 0, out
    assert "clean" in out


def test_run_on_real_repo() -> None:
    """Smoke: run against the real repo defaults (integration, not assertion-heavy)."""
    if not SCRIPT.exists():
        pytest.skip("script not present")
    repo = Path(__file__).resolve().parents[1]
    ep = repo / ".csp" / "code-spec" / "saw" / "entry-points.jsonl"
    if not ep.exists():
        pytest.skip("entry-points.jsonl not present")
    r = subprocess.run(
        ["/bin/bash", str(SCRIPT)], cwd=repo, capture_output=True, text=True
    )
    # Either clean (0) or stale found (1) — must not crash (>1).
    assert r.returncode in (0, 1), r.stdout + r.stderr
    assert "mcp tools:" in r.stdout
