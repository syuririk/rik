"""Currency vocabulary (ISO 4217 subset relevant to rik data sources)."""

from __future__ import annotations

from enum import StrEnum


class Currency(StrEnum):
    """ISO 4217 currency codes.

    Subset covering the markets rikcore currently sources. Extend as new
    sources are added — adding a member is a minor (backward-compatible)
    change as long as existing members keep their values.
    """

    KRW = "KRW"
    USD = "USD"
    EUR = "EUR"
    JPY = "JPY"
    GBP = "GBP"
    CNY = "CNY"
    HKD = "HKD"

    # Sentinel for unit-less data (indices, ratios, macro indicators).
    NONE = "NONE"
