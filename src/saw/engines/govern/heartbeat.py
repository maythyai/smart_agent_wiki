"""D3 (v1.26.0): heartbeat-driven proactive patrol (Letta-inspired).

Letta's heartbeat runs an agent's "brain" at intervals (not just on user input)
for proactive memory management. SAW lands this as a Governor/Detector patrol:
a BackgroundScheduler runs freshness + unresolved-contradiction scans on an
interval (env-configurable), so stale claims and open contradictions surface
without a user-triggered `saw freshness`/`saw conflicts`. Pure-stdlib +
apscheduler (a SAW dep); no LLM, no network.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class HeartbeatScheduler:
    """Proactive patrol scheduler for the governance engine.

    Args:
        governor: Governor (freshness report).
        detector: ContradictionDetector (unresolved contradictions).
        interval_seconds: Patrol cadence (default 300s; override via
            ``SAW_HEARTBEAT_INTERVAL`` env). <=0 disables.
    """

    def __init__(self, governor=None, detector=None, interval_seconds: int | None = None) -> None:
        self._governor = governor
        self._detector = detector
        self._interval = interval_seconds if interval_seconds is not None else int(
            os.environ.get("SAW_HEARTBEAT_INTERVAL", "300")
        )
        self._scheduler = None
        self._last_run: dict[str, Any] | None = None

    @property
    def last_run(self) -> dict | None:
        return self._last_run

    def start(self) -> bool:
        """Start the background patrol. Returns False if disabled/unavailable."""
        if self._interval <= 0 or self._governor is None:
            self._last_run = {"status": "disabled", "reason": "no governor or interval<=0"}
            return False
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
        except ImportError:
            self._last_run = {"status": "disabled", "reason": "apscheduler not installed"}
            return False
        self._scheduler = BackgroundScheduler(daemon=True)
        self._scheduler.add_job(self._patrol, "interval", seconds=self._interval, id="saw-heartbeat")
        self._scheduler.start()
        logger.info("Heartbeat patrol started (interval=%ss)", self._interval)
        return True

    def stop(self) -> None:
        if self._scheduler is not None:
            try:
                self._scheduler.shutdown(wait=False)
            except Exception:
                pass
            self._scheduler = None

    def _patrol(self) -> None:
        """One patrol tick: freshness report + unresolved contradictions count."""
        ts = datetime.now(timezone.utc).isoformat()
        fresh = None
        unresolved = None
        try:
            if hasattr(self._governor, "get_freshness_report"):
                fresh = self._governor.get_freshness_report()
        except Exception as e:  # patrol must never raise
            logger.warning("heartbeat freshness patrol failed: %s", e)
        try:
            if self._detector is not None and hasattr(self._detector, "get_unresolved_contradictions"):
                unresolved = len(self._detector.get_unresolved_contradictions())
        except Exception as e:
            logger.warning("heartbeat contradiction patrol failed: %s", e)
        self._last_run = {
            "status": "ok",
            "ran_at": ts,
            "interval_seconds": self._interval,
            "stale_count": self._stale_count(fresh),
            "unresolved_contradictions": unresolved,
        }
        logger.info("heartbeat patrol: %s", self._last_run)

    @staticmethod
    def _stale_count(report) -> int | None:
        """Best-effort: count aging+stale claims from a freshness report."""
        if report is None:
            return None
        for attr in ("stale_count", "aging_count", "stale", "total_stale"):
            if hasattr(report, attr):
                try:
                    return int(getattr(report, attr))
                except (TypeError, ValueError):
                    pass
        return None
