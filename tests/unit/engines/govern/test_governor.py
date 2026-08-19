"""Regression tests for the Governor human-review queue.

trigger_review / get_review_queue were previously no-op placeholders that
always returned []; they now keep real (in-process) state.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from saw.engines.govern.governor import Governor


def _governor() -> Governor:
    # Linter is constructed inside Governor.__init__; Mock repos are enough
    # since these tests only exercise the review-queue state, not DB queries.
    return Governor(MagicMock(), MagicMock())


def test_trigger_review_records_uuids():
    gov = _governor()
    assert gov.get_review_queue() == []
    gov.trigger_review(["c-1", "c-2", "c-3"])
    assert gov.get_review_queue() == ["c-1", "c-2", "c-3"]


def test_trigger_review_is_idempotent_and_sorted():
    gov = _governor()
    gov.trigger_review(["c-3", "c-1"])
    gov.trigger_review(["c-1", "c-2"])  # duplicates ignored
    assert gov.get_review_queue() == ["c-1", "c-2", "c-3"]


def test_trigger_review_ignores_empty_and_falsy():
    gov = _governor()
    gov.trigger_review(["", None, "c-1"])
    assert gov.get_review_queue() == ["c-1"]
