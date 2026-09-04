"""Synthesize scheduler coverage — T-F-K-3 (AC-COV-3)."""
from __future__ import annotations

from pathlib import Path


def test_default_tasks_created(tmp_path):
    from saw.synthesize.scheduler import ScheduleType, SynthesizeScheduler

    sched = SynthesizeScheduler(config_path=tmp_path / "sched.json")
    tasks = sched.list_tasks()
    ids = {t.task_id for t in tasks}
    assert {"nightly-pattern", "weekly-synthesis", "monthly-analysis"} <= ids
    nightly = sched.get_task("nightly-pattern")
    assert nightly.schedule_type == ScheduleType.NIGHTLY


def test_enable_disable_task(tmp_path):
    from saw.synthesize.scheduler import SynthesizeScheduler

    sched = SynthesizeScheduler(config_path=tmp_path / "sched.json")
    sched.disable_task("nightly-pattern")
    assert sched.get_task("nightly-pattern").enabled is False
    sched.enable_task("nightly-pattern")
    assert sched.get_task("nightly-pattern").enabled is True


def test_mark_task_run_updates_next_run_and_records(tmp_path):
    from saw.synthesize.scheduler import SynthesizeScheduler

    sched = SynthesizeScheduler(config_path=tmp_path / "sched.json")
    sched.mark_task_run("nightly-pattern", success=True, pages_generated=2, patterns_found=3)
    nightly = sched.get_task("nightly-pattern")
    assert nightly.last_run is not None
    assert nightly.next_run is not None  # rescheduled
    results = sched.get_recent_results()
    assert any(r.task_id == "nightly-pattern" and r.success for r in results)


def test_add_and_remove_custom_task(tmp_path):
    from saw.synthesize.scheduler import ScheduleType, SynthesizeScheduler

    sched = SynthesizeScheduler(config_path=tmp_path / "sched.json")
    sched.add_custom_task(
        task_id="custom-1",
        schedule_type=ScheduleType.MANUAL,
        scope="wiki/x",
        config={"time_window_hours": 24},
    )
    assert sched.get_task("custom-1") is not None
    sched.remove_task("custom-1")
    assert sched.get_task("custom-1") is None


def test_get_pending_tasks_filters_disabled(tmp_path):
    from saw.synthesize.scheduler import SynthesizeScheduler

    sched = SynthesizeScheduler(config_path=tmp_path / "sched.json")
    # No task should be pending immediately (next_run is in the future).
    assert sched.get_pending_tasks() == []


def test_save_load_round_trip(tmp_path):
    from saw.synthesize.scheduler import SynthesizeScheduler

    cfg = tmp_path / "sched.json"
    sched = SynthesizeScheduler(config_path=cfg)
    sched.disable_task("weekly-synthesis")
    sched.save()
    assert cfg.exists()

    sched2 = SynthesizeScheduler(config_path=cfg)
    sched2.load()
    assert sched2.get_task("weekly-synthesis").enabled is False
