"""Standard record types — the data contract between rikcore and rikfeed."""

from __future__ import annotations

from rikschema.records.base import KST, StandardRecord
from rikschema.records.fundamental import FundamentalRecord, PeriodType
from rikschema.records.macro import Frequency, MacroRecord
from rikschema.records.metadata import InstrumentMeta
from rikschema.records.ohlcv import OHLCVRecord

__all__ = [
    "KST",
    "StandardRecord",
    "OHLCVRecord",
    "FundamentalRecord",
    "PeriodType",
    "MacroRecord",
    "Frequency",
    "InstrumentMeta",
]
