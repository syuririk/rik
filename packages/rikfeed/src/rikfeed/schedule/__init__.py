"""Scheduling for feed runs.

A thin, dependency-free description of when a feed job should run (post-KRX
close). The actual trigger (cron, APScheduler, Colab cell) is left to the
deployment; this module just computes the next run time so the policy lives
in one place.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta

from rikschema.records.base import KST

# KRX regular session closes 15:30 KST; collect a margin after.
KRX_CLOSE = time(15, 30)
DEFAULT_MARGIN_MINUTES = 30


def next_run_after(
    now: datetime | None = None,
    *,
    close: time = KRX_CLOSE,
    margin_minutes: int = DEFAULT_MARGIN_MINUTES,
) -> datetime:
    """Next KST datetime to run the feed (close + margin, weekdays only)."""
    now = (now or datetime.now(KST)).astimezone(KST)
    run_time = (
        datetime.combine(now.date(), close, tzinfo=KST)
        + timedelta(minutes=margin_minutes)
    )
    # if today's slot has passed or it's the weekend, roll forward
    candidate = run_time
    if candidate <= now:
        candidate += timedelta(days=1)
    while candidate.weekday() >= 5:  # Sat/Sun
        candidate += timedelta(days=1)
    return candidate


__all__ = ["next_run_after", "KRX_CLOSE"]
