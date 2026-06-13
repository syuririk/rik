"""rikschema — the data & behavior contract for the rik ecosystem.

Pure contract package: depends only on pydantic. Producers (rikcore) and
consumers (rikfeed) both depend on this and on nothing of each other.
"""

from __future__ import annotations

from rikschema.enums import AssetClass, Currency, SourceId
from rikschema.errors import (
    FetchError,
    NormalizationError,
    RikError,
    SchemaError,
    SourceError,
    SymbolResolutionError,
    ValidationFailure,
)
from rikschema.interfaces import Emitter, Source
from rikschema.records import (
    KST,
    Frequency,
    FundamentalRecord,
    InstrumentMeta,
    MacroRecord,
    OHLCVRecord,
    PeriodType,
    StandardRecord,
)
from rikschema.version import __version__

__all__ = [
    "__version__",
    # enums
    "AssetClass",
    "Currency",
    "SourceId",
    # records
    "StandardRecord",
    "OHLCVRecord",
    "FundamentalRecord",
    "PeriodType",
    "MacroRecord",
    "Frequency",
    "InstrumentMeta",
    "KST",
    # interfaces
    "Source",
    "Emitter",
    # errors
    "RikError",
    "SchemaError",
    "SourceError",
    "FetchError",
    "NormalizationError",
    "SymbolResolutionError",
    "ValidationFailure",
]
