"""FinanceDataReader source adapter (KR equities, indices, ETFs).

Replaces the old pykrx adapter. As of early 2026 the KRX site changes broke
pykrx (auth required, many endpoints 404); FinanceDataReader scrapes from
working endpoints and needs no credentials.

`fdr.DataReader(symbol, start, end)` returns a DataFrame with a DatetimeIndex
named "Date" and plain English columns (Open/High/Low/Close/[Adj Close]/
Volume) — the same shape as yfinance after flattening, so the transform is
straightforward. fdr is lazy-imported in fetch() so the rest of rikcore loads
without the dependency.
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


class FDRSource(SourceAdapter):
    """Fetches daily bars from FinanceDataReader."""

    source_id = SourceId.FDR

    def fetch(self, symbols: list[str], start: date, end: date) -> dict[str, Any]:
        try:
            import FinanceDataReader as fdr
        except ImportError as exc:  # pragma: no cover
            raise FetchError(
                "FinanceDataReader not installed (pip install finance-datareader)",
                source_id=self.source_id.value,
            ) from exc

        out: dict[str, Any] = {}
        for canonical in symbols:
            native = self.resolver.to_native(canonical, self.source_id)
            try:
                df = fdr.DataReader(native, start, end)
            except Exception as exc:  # pragma: no cover - network
                raise FetchError(
                    f"DataReader failed for {native}",
                    source_id=self.source_id.value,
                ) from exc
            out[canonical] = {
                "native": native,
                "records": self._frame_to_rows(df),
            }
        return out

    @staticmethod
    def _frame_to_rows(df: Any) -> list[dict[str, Any]]:
        """DataFrame -> row dicts. FDR uses a DatetimeIndex named 'Date'."""
        if df is None or len(df) == 0:
            return []
        return df.reset_index().to_dict("records")

    def to_standard(self, raw: dict[str, Any]) -> list[StandardRecord]:
        records: list[StandardRecord] = []
        for canonical, payload in raw.items():
            asset_class = self._infer_asset_class(canonical)
            currency = self._infer_currency(canonical)
            for row in payload["records"]:
                records.append(
                    self._row_to_record(canonical, asset_class, currency, row)
                )
        return records

    def _row_to_record(
        self,
        symbol: str,
        asset_class: AssetClass,
        currency: Currency,
        row: dict[str, Any],
    ) -> OHLCVRecord:
        ts = (
            row.get("Date")
            or row.get("index")  # reset_index() on an unnamed index, just in case
        )
        if ts is None:
            raise NormalizationError(
                f"no date column in row (keys={list(row)})", field="Date"
            )
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
                currency=currency,
                adjusted=False,
            )
        except KeyError as exc:
            raise NormalizationError(
                f"missing OHLC column {exc}", field=str(exc)
            ) from exc

    @staticmethod
    def _infer_asset_class(symbol: str) -> AssetClass:
        if symbol.startswith("INDEX:"):
            return AssetClass.EQUITY_INDEX
        if symbol.startswith("ETF:"):
            return AssetClass.ETF
        return AssetClass.EQUITY

    @staticmethod
    def _infer_currency(symbol: str) -> Currency:
        # FDR KR indices (KS11/KQ11) are unit-less; KR equities/ETFs are KRW.
        if symbol.startswith("INDEX:"):
            return Currency.NONE
        return Currency.KRW
