"""rikcore — multi-source market data collection & standardization.

Producer side of the rik ecosystem: implements rikschema.Source adapters,
normalizes heterogeneous source data into rikschema standard records, and
emits them for rikfeed to consume.
"""

from __future__ import annotations

from rikcore.emit import DataFrameEmitter, DictEmitter, RecordsEmitter
from rikcore.normalize import SymbolResolver
from rikcore.pipeline import Orchestrator, PipelineResult
from rikcore.sources import (
    ManualSource,
    PyKRXSource,
    SourceRegistry,
    YFinanceSource,
)
from rikcore.validate import validate_batch

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Orchestrator",
    "PipelineResult",
    "SourceRegistry",
    "SymbolResolver",
    "ManualSource",
    "YFinanceSource",
    "PyKRXSource",
    "RecordsEmitter",
    "DictEmitter",
    "DataFrameEmitter",
    "validate_batch",
]
