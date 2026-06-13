"""Standard fundamental / financial-statement record.

Fundamentals are sparse and heterogeneous across instruments, so instead of
a fixed wide schema (hundreds of nullable columns), each record is a single
(metric, value) point in time. The `period` distinguishes the reporting
window the value belongs to vs. `timestamp` (when it was reported/observed).
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import Field

from rikschema.enums import Currency
from rikschema.records.base import StandardRecord


class PeriodType(StrEnum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    TTM = "ttm"            # trailing twelve months
    POINT = "point"        # point-in-time snapshot (e.g. market cap)


class FundamentalRecord(StandardRecord):
    """A single fundamental metric observation.

    Example: {symbol: "KRX:005930", metric: "revenue",
              value: 2.79e14, period_type: ANNUAL, period_end: 2024-12-31}
    """

    metric: str = Field(min_length=1)   # e.g. "revenue", "eps", "per", "roe"
    value: float
    period_type: PeriodType
    period_end: date                    # close of the reporting window
    currency: Currency = Currency.NONE  # NONE for ratios (PER, ROE, ...)
    unit: str | None = None             # free-form, e.g. "ratio", "%", "shares"
