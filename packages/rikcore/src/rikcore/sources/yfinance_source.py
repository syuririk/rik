"""yfinance source adapter.

Imports yfinance lazily inside fetch() so the rest of rikcore (and its tests)
load without the dependency present. The to_standard transform is pure and
network-free, so it can be tested against recorded fixtures.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from rikschema import (
    AssetClass,
    Currency,
    FetchError,
    NormalizationError,
    OHLCVRecord,
    SourceId,
    StandardRecord,
)

from rikcore.normalize import SymbolResolver, to_kst_midnight
from rikcore.sources.base import SourceAdapter

# yfinance column -> standard field
_COLUMN_MAP = {
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Volume": "volume",
}


class YFinanceSource(SourceAdapter):
    """Fetches daily bars from Yahoo Finance via yfinance."""

    source_id = SourceId.YFINANCE

    def fetch(self, symbols: list[str], start: date, end: date) -> dict[str, Any]:
        try:
            import yfinance as yf
        except ImportError as exc:  # pragma: no cover
            raise FetchError(
                "yfinance not installed", source_id=self.source_id.value
            ) from exc

        out: dict[str, Any] = {}
        for canonical in symbols:
            native = self.resolver.to_native(canonical, self.source_id)
            try:
                df = yf.download(
                    native, start=start, end=end, progress=False, auto_adjust=False
                )
            except Exception as exc:  # pragma: no cover - network
                raise FetchError(
                    f"download failed for {native}", source_id=self.source_id.value
                ) from exc
            # carry canonical id + native rows forward to the pure transform
            out[canonical] = {
                "native": native,
                "records": df.reset_index().to_dict("records") if df is not None else [],
            }
        return out

    def to_standard(self, raw: dict[str, Any]) -> list[StandardRecord]:
        records: list[StandardRecord] = []
        for canonical, payload in raw.items():
            asset_class = self._infer_asset_class(canonical)
            for row in payload["records"]:
                records.append(self._row_to_record(canonical, asset_class, row))
        return records

    def _row_to_record(
        self, symbol: str, asset_class: AssetClass, row: dict[str, Any]
    ) -> OHLCVRecord:
        ts = row.get("Date") or row.get("Datetime")
        if ts is None:
            raise NormalizationError("missing Date column", field="Date")
        day = ts.date() if hasattr(ts, "date") else ts
        try:
            return OHLCVRecord(
                symbol=symbol,
                timestamp=to_kst_midnight(day),
                source=self.source_id,
                asset_class=asset_class,
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row.get("Volume", 0) or 0),
                currency=self._infer_currency(symbol),
                adjusted=False,
            )
        except KeyError as exc:
            raise NormalizationError("missing OHLC column", field=str(exc)) from exc

    @staticmethod
    def _infer_asset_class(symbol: str) -> AssetClass:
        if symbol.startswith("INDEX:"):
            return AssetClass.EQUITY_INDEX
        if symbol.startswith("ETF:"):
            return AssetClass.ETF
        return AssetClass.EQUITY

    @staticmethod
    def _infer_currency(symbol: str) -> Currency:
        if symbol.startswith(("KRX:", "INDEX:KOSPI", "INDEX:KOSDAQ")):
            return Currency.KRW
        if symbol.startswith("INDEX:"):
            return Currency.NONE
        return Currency.USD
