"""Standard OHLCV (price/volume) record."""

from __future__ import annotations

from pydantic import Field, model_validator

from rikschema.enums import Currency
from rikschema.records.base import StandardRecord


class OHLCVRecord(StandardRecord):
    """One bar of open/high/low/close/volume data.

    `currency` is NONE for unit-less series (indices). Prices are stored in
    the instrument's native currency — rikcore does NOT auto-convert; any
    FX conversion is an explicit downstream transform so the raw record
    stays faithful to the source.
    """

    open: float = Field(ge=0)
    high: float = Field(ge=0)
    low: float = Field(ge=0)
    close: float = Field(ge=0)
    volume: float = Field(ge=0, default=0.0)
    currency: Currency = Currency.NONE
    adjusted: bool = False  # True if close is split/dividend adjusted

    @model_validator(mode="after")
    def _check_ohlc_consistency(self) -> "OHLCVRecord":
        if self.high < self.low:
            raise ValueError(f"high ({self.high}) < low ({self.low})")
        if not (self.low <= self.open <= self.high):
            raise ValueError(f"open ({self.open}) outside [low, high]")
        if not (self.low <= self.close <= self.high):
            raise ValueError(f"close ({self.close}) outside [low, high]")
        return self
