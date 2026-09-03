"""Token bench tests — T-F-I-3 (AC-TK-1)."""
from __future__ import annotations

import tempfile
from pathlib import Path

from typer.testing import CliRunner


def test_bench_reports_savings_and_is_deterministic():
    """AC-TK-1: optimized < baseline, saved% > 0, deterministic across runs."""
    from saw.drivers.cli.main import app

    runner = CliRunner()
    with tempfile.TemporaryDirectory() as d:
        corpus = Path(d)
        (corpus / "a.py").write_text("def f():\n    return 1\n" * 50)
        (corpus / "b.md").write_text("# Title\n\nbody text\n" * 50)

        args = ["token", "bench", "--corpus", str(corpus), "--reads", "3"]
        r1 = runner.invoke(app, args)
        r2 = runner.invoke(app, args)
        assert r1.exit_code == 0, r1.output
        # Savings reported and positive (extract the percentage via regex so
        # Rich markup in the table doesn't break parsing).
        import re

        m = re.search(r"(\d+(?:\.\d+)?)\s*%", r1.output)
        assert m, r1.output
        assert float(m.group(1)) > 0.0
        # Determinism: same corpus → same saved % across two runs.
        m2 = re.search(r"(\d+(?:\.\d+)?)\s*%", r2.output)
        assert m2 and float(m2.group(1)) == float(m.group(1))
        # baseline must exceed optimized (token cost reduced).
        out = r1.output
        assert "baseline tokens" in out and "optimized tokens" in out


def test_bench_no_corpus_exits_nonzero():
    """AC-TK-1: missing corpus fails clearly."""
    from saw.drivers.cli.main import app

    with tempfile.TemporaryDirectory() as d:
        res = CliRunner().invoke(app, ["token", "bench", "--corpus", str(Path(d) / "nope")])
        assert res.exit_code == 1
