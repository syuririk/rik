"""Asset class vocabulary shared across the rik ecosystem."""

from __future__ import annotations

from enum import StrEnum


class AssetClass(StrEnum):
    """Top-level asset classification.

    Kept deliberately coarse — fine-grained sub-types belong in metadata,
    not in this enum, so that adding a niche instrument never forces a
    schema-breaking change here.
    """

    EQUITY = "equity"            # individual stocks
    EQUITY_INDEX = "equity_index"  # KOSPI, S&P 500, ...
    ETF = "etf"
    BOND = "bond"
    COMMODITY = "commodity"
    FX = "fx"
    CRYPTO = "crypto"
    MACRO = "macro"              # economic indicators (GDP, CPI, rates)
    OTHER = "other"
