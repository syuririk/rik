"""Trading-calendar and timestamp alignment helpers."""

from __future__ import annotations

from datetime import date, datetime, time

from rikschema.records.base import KST


def to_kst_midnight(d: date) -> datetime:
    """A calendar date -> KST-aware datetime at 00:00.

    Used for daily bars / macro observations where only the date matters but
    StandardRecord requires a tz-aware timestamp.
    """
    return datetime.combine(d, time(0, 0), tzinfo=KST)


def is_weekday(d: date) -> bool:
    return d.weekday() < 5  # Mon-Fri


def daterange(start: date, end: date):
    """Inclusive day iterator from start to end."""
    from datetime import timedelta

    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)
