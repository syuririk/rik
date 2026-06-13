"""Canonical source identifiers.

Every BaseSource implementation in rikcore declares one of these as its
`source_id`. Stamping records with their origin makes provenance explicit
and lets rikfeed deduplicate / prioritise across overlapping sources.
"""

from __future__ import annotations

from enum import StrEnum


class SourceId(StrEnum):
    YFINANCE = "yfinance"
    FDR = "fdr"  # FinanceDataReader (KR equities, indices, ETFs)
    DART = "dart"
    OECD = "oecd"
    MANUAL = "manual"  # hand-entered / overrides
