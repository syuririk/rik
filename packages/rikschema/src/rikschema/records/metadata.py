"""Instrument metadata — the symbol-resolution backbone.

Unlike the time-series records, an `InstrumentMeta` is a *reference* entry:
one per canonical instrument, carrying the cross-source ticker aliases that
let rikcore's symbol_resolver map any source's native ticker to the single
canonical `symbol`.

This is the record type that makes multi-source merging possible: when
yfinance says "005930.KS" and FDR says "005930", both resolve to the one
canonical symbol declared here.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from rikschema.enums import AssetClass, Currency, SourceId


class InstrumentMeta(BaseModel):
    """Reference metadata for one canonical instrument.

    Not a StandardRecord: it has no timestamp (it's reference data, not an
    observation). It carries its own provenance-agnostic aliases instead.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    symbol: str = Field(min_length=1)   # canonical id, e.g. "KRX:005930"
    name: str = Field(min_length=1)     # human-readable, e.g. "Samsung Electronics"
    asset_class: AssetClass
    currency: Currency = Currency.NONE

    # source ticker aliases: {SourceId.YFINANCE: "005930.KS", ...}
    aliases: dict[SourceId, str] = Field(default_factory=dict)

    country: str | None = None          # ISO 3166-1 alpha-2, e.g. "KR"
    exchange: str | None = None         # e.g. "KRX", "NYSE"

    @field_validator("symbol")
    @classmethod
    def _strip_symbol(cls, v: str) -> str:
        return v.strip()

    def alias_for(self, source: SourceId) -> str | None:
        """Return this instrument's native ticker for a given source."""
        return self.aliases.get(source)
