"""A network-free source adapter.

Takes pre-built OHLCV rows in memory and emits standard records. Useful for
tests, fixtures, overrides, and seeding — and as the simplest reference
implementation of the Source protocol.
"""

from __future__ import annotations

from datetime import date
from typing import Any, TypedDict

from rikschema import AssetClass, Currency, OHLCVRecord, SourceId, StandardRecord

from rikcore.normalize import SymbolResolver, to_kst_midnight
from rikcore.sources.base import SourceAdapter


class ManualRow(TypedDict):
    symbol: str          # canonical id
    day: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    currency: Currency
    asset_class: AssetClass


class ManualSource(SourceAdapter):
    """Emit standard OHLCV records from in-memory rows. No I/O."""

    source_id = SourceId.MANUAL

    def __init__(self, resolver: SymbolResolver, rows: list[ManualRow]) -> None:
        super().__init__(resolver)
        self._rows = rows

    def fetch(self, symbols: list[str], start: date, end: date) -> list[ManualRow]:
        wanted = set(symbols)
        return [
            r for r in self._rows
            if r["symbol"] in wanted and start <= r["day"] <= end
        ]

    def to_standard(self, raw: Any) -> list[StandardRecord]:
        out: list[StandardRecord] = []
        for r in raw:
            out.append(
                OHLCVRecord(
                    symbol=r["symbol"],
                    timestamp=to_kst_midnight(r["day"]),
                    source=self.source_id,
                    asset_class=r["asset_class"],
                    open=r["open"],
                    high=r["high"],
                    low=r["low"],
                    close=r["close"],
                    volume=r["volume"],
                    currency=r["currency"],
                )
            )
        return out
