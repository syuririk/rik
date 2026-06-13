"""Standard macroeconomic indicator record.

Bridges econkit / OECD SDMX style data into the rik schema. A macro series
is a (indicator, value) point in time, keyed by a canonical symbol such as
"MACRO:KR.CPI" or "MACRO:US.GDP".
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from rikschema.records.base import StandardRecord


class Frequency(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class MacroRecord(StandardRecord):
    """One observation of a macroeconomic indicator.

    `timestamp` is the reference period start (normalized to KST midnight by
    the base validator). `frequency` tells consumers how to align / resample.
    """

    indicator: str = Field(min_length=1)  # e.g. "CPI", "GDP", "policy_rate"
    value: float
    frequency: Frequency
    unit: str | None = None               # "index", "%", "pct_yoy", ...
    seasonally_adjusted: bool = False
