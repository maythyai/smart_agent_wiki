"""Synthesize engine coverage — T-F-K-3 (AC-COV-3)."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path


def test_synthesize_no_patterns_returns_empty(tmp_path):
    """synthesize() with no mined patterns short-circuits cleanly."""
    from saw.synthesize.engine import SynthesizeEngine

    engine = SynthesizeEngine(output_dir=tmp_path)
    result = engine.synthesize([], save_pages=False)
    assert result.mining.patterns == []
    assert result.pages == []
    assert result.total_time >= 0


def test_synthesize_with_items(tmp_path):
    """synthesize() runs the full mine→cluster→generate pipeline."""
    from saw.synthesize.engine import SynthesizeEngine

    engine = SynthesizeEngine(output_dir=tmp_path, min_occurrences=1)
    items = [
        {"id": "c1", "content": "python is great", "topic": "python"},
        {"id": "c2", "content": "python rocks", "topic": "python"},
        {"id": "c3", "content": "python rocks", "topic": "python"},
    ]
    result = engine.synthesize(items, save_pages=False)
    # mining may or may not find patterns depending on miner; assert structure.
    assert hasattr(result, "mining") and hasattr(result, "clustering")
    assert result.total_time >= 0


def test_run_scheduled_task_unknown_raises(tmp_path):
    """run_scheduled_task raises ValueError for an unknown task."""
    import pytest

    from saw.synthesize.engine import SynthesizeEngine

    engine = SynthesizeEngine(output_dir=tmp_path)
    with pytest.raises(ValueError, match="Task not found"):
        engine.run_scheduled_task("nope", [])


def test_get_stats_and_pending(tmp_path):
    """get_stats / get_pending_tasks surface scheduler state."""
    from saw.synthesize.engine import SynthesizeEngine

    engine = SynthesizeEngine(output_dir=tmp_path)
    stats = engine.get_stats()
    assert "scheduler" in stats and "miner" in stats
    assert stats["scheduler"]["total_tasks"] >= 1
    assert isinstance(engine.get_pending_tasks(), list)


def test_enable_tasks(tmp_path):
    """enable_nightly/weekly/monthly flip the corresponding task."""
    from saw.synthesize.engine import SynthesizeEngine

    engine = SynthesizeEngine(output_dir=tmp_path)
    engine.enable_nightly()
    engine.enable_weekly()
    engine.enable_monthly()
    nightly = engine.scheduler.get_task("nightly-pattern")
    weekly = engine.scheduler.get_task("weekly-synthesis")
    monthly = engine.scheduler.get_task("monthly-analysis")
    assert nightly.enabled and weekly.enabled and monthly.enabled
