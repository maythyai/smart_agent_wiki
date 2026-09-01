"""T-F-A-1-1: smoke command skeleton — node runner + exit code.

The skeleton runs registered smoke nodes, prints per-node PASS/FAIL+duration,
and returns/exits non-zero on any failure. Engine-node bodies are F-A-2..4
(later Wave 2); here we test the runner contract. AC-E2E-1 (partial).
"""
from __future__ import annotations

import time

import pytest
import typer
from typer.testing import CliRunner

from saw.drivers.cli.commands.smoke_cmd import SmokeNode, run_smoke, smoke


def _app_with_smoke() -> typer.Typer:
    t = typer.Typer()
    t.command(name="smoke")(smoke)
    return t


def _ok() -> bool:
    return True


def _bad() -> bool:
    return False


def _raise() -> bool:
    raise RuntimeError("boom")


def test_run_smoke_all_pass(capsys: pytest.CaptureFixture[str]) -> None:
    nodes = [SmokeNode("a", _ok), SmokeNode("b", _ok)]
    failed = run_smoke(nodes)
    out = capsys.readouterr().out
    assert failed == 0
    assert "PASS a" in out
    assert "PASS b" in out


def test_run_smoke_fail_marks_and_counts(capsys: pytest.CaptureFixture[str]) -> None:
    nodes = [SmokeNode("ok", _ok), SmokeNode("bad", _bad)]
    failed = run_smoke(nodes)
    out = capsys.readouterr().out
    assert failed == 1
    assert "PASS ok" in out
    assert "FAIL bad" in out


def test_run_smoke_exception_is_failure(capsys: pytest.CaptureFixture[str]) -> None:
    nodes = [SmokeNode("boom", _raise)]
    failed = run_smoke(nodes)
    out = capsys.readouterr().out
    assert failed == 1
    assert "FAIL boom" in out
    assert "boom" in out  # error context surfaced


def test_smoke_command_exit_code() -> None:
    runner = CliRunner()
    # skeleton self-check nodes should all pass → exit 0
    result = runner.invoke(_app_with_smoke(), ["smoke", "--self-check"])
    assert result.exit_code == 0, result.output
    assert "PASS" in result.output


def test_smoke_command_reports_duration() -> None:
    runner = CliRunner()
    result = runner.invoke(_app_with_smoke(), ["smoke", "--self-check"])
    assert "s" in result.output  # duration printed per node
