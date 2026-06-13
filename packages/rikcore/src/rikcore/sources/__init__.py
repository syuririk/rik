"""Source adapters: one per data origin, all satisfying rikschema.Source."""

from __future__ import annotations

from rikcore.sources.base import SourceAdapter
from rikcore.sources.fdr_source import FDRSource
from rikcore.sources.manual_source import ManualRow, ManualSource
from rikcore.sources.registry import SourceRegistry
from rikcore.sources.yfinance_source import YFinanceSource

__all__ = [
    "SourceAdapter",
    "SourceRegistry",
    "ManualSource",
    "ManualRow",
    "YFinanceSource",
    "FDRSource",
]
