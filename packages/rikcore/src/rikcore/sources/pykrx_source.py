"""pykrx source adapter (KRX market data).

Lazy-imports pykrx in fetch(). The to_standard transform handles pykrx's
Korean column names and is pure / testable with fixtures.
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

# pykrx Korean column -> standard field
_COLUMN_MAP = {
    "시가": "open",
    "고가": "high",
    "저가": "low",
    "종가": "close",
    "거래량": "volume",
}


def _yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")


class PyKRXSource(SourceAdapter):
    """Fetches daily KRX bars via pykrx."""

    source_id = SourceId.PYKRX

    def fetch(self, symbols: list[str], start: date, end: date) -> dict[str, Any]:
        try:
            from pykrx import stock
        except ImportError as exc:  # pragma: no cover
            raise FetchError(
                "pykrx not installed", source_id=self.source_id.value
            ) from exc

        out: dict[str, Any] = {}
        for canonical in symbols:
            native = self.resolver.to_native(canonical, self.source_id)
            try:
                df = stock.get_market_ohlcv(
                    _yyyymmdd(start), _yyyymmdd(end), native
                )
            except Exception as exc:  # pragma: no cover - network
                raise FetchError(
                    f"ohlcv failed for {native}", source_id=self.source_id.value
                ) from exc
            out[canonical] = {
                "native": native,
                "records": df.reset_index().to_dict("records") if df is not None else [],
            }
        return out

    def to_standard(self, raw: dict[str, Any]) -> list[StandardRecord]:
        records: list[StandardRecord] = []
        for canonical, payload in raw.items():
            for row in payload["records"]:
                records.append(self._row_to_record(canonical, row))
        return records

    def _row_to_record(self, symbol: str, row: dict[str, Any]) -> OHLCVRecord:
        ts = row.get("날짜") or row.get("date")
        if ts is None:
            raise NormalizationError("missing 날짜 column", field="날짜")
        day = ts.date() if hasattr(ts, "date") else ts
        mapped = {std: row[src] for src, std in _COLUMN_MAP.items() if src in row}
        missing = set(_COLUMN_MAP.values()) - set(mapped) - {"volume"}
        if missing:
            raise NormalizationError(
                f"missing columns: {sorted(missing)}", field=str(sorted(missing))
            )
        return OHLCVRecord(
            symbol=symbol,
            timestamp=to_kst_midnight(day),
            source=self.source_id,
            asset_class=AssetClass.EQUITY,
            open=float(mapped["open"]),
            high=float(mapped["high"]),
            low=float(mapped["low"]),
            close=float(mapped["close"]),
            volume=float(mapped.get("volume", 0) or 0),
            currency=Currency.KRW,
        )
