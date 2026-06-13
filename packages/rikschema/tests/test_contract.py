"""Tests for the rikschema contract invariants."""

from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from rikschema import (
    AssetClass,
    Currency,
    Emitter,
    FundamentalRecord,
    InstrumentMeta,
    OHLCVRecord,
    PeriodType,
    Source,
    SourceId,
    StandardRecord,
)
from rikschema.records.base import KST

UTC_NOON = datetime(2025, 1, 2, 12, 0, tzinfo=timezone.utc)


def _ohlcv(**overrides) -> OHLCVRecord:
    base = dict(
        symbol="KRX:005930",
        timestamp=UTC_NOON,
        source=SourceId.PYKRX,
        asset_class=AssetClass.EQUITY,
        open=100.0,
        high=110.0,
        low=95.0,
        close=105.0,
        volume=1000.0,
        currency=Currency.KRW,
    )
    base.update(overrides)
    return OHLCVRecord(**base)


class TestTimestampNormalization:
    def test_naive_timestamp_rejected(self):
        with pytest.raises(ValueError, match="timezone-aware"):
            _ohlcv(timestamp=datetime(2025, 1, 2, 12, 0))

    def test_aware_timestamp_converted_to_kst(self):
        rec = _ohlcv()
        assert rec.timestamp.tzinfo == KST
        # UTC noon -> KST 21:00 same day
        assert rec.timestamp.hour == 21

    def test_other_tz_converted_to_kst(self):
        ny = datetime(2025, 1, 2, 9, 30, tzinfo=ZoneInfo("America/New_York"))
        rec = _ohlcv(timestamp=ny)
        assert rec.timestamp.tzinfo == KST


class TestOHLCVConsistency:
    def test_high_below_low_rejected(self):
        with pytest.raises(ValueError, match="high"):
            _ohlcv(high=90.0, low=95.0)

    def test_close_outside_range_rejected(self):
        with pytest.raises(ValueError, match="close"):
            _ohlcv(close=200.0)

    def test_negative_price_rejected(self):
        with pytest.raises(ValueError):
            _ohlcv(open=-1.0)


class TestStrictness:
    def test_extra_field_forbidden(self):
        with pytest.raises(ValueError):
            _ohlcv(bogus_field=123)

    def test_record_is_frozen(self):
        rec = _ohlcv()
        with pytest.raises(Exception):
            rec.close = 999.0  # type: ignore[misc]

    def test_empty_symbol_rejected(self):
        with pytest.raises(ValueError, match="symbol"):
            _ohlcv(symbol="   ")


class TestFundamental:
    def test_construct(self):
        rec = FundamentalRecord(
            symbol="KRX:005930",
            timestamp=UTC_NOON,
            source=SourceId.DART,
            asset_class=AssetClass.EQUITY,
            metric="revenue",
            value=2.79e14,
            period_type=PeriodType.ANNUAL,
            period_end=date(2024, 12, 31),
            currency=Currency.KRW,
        )
        assert rec.metric == "revenue"
        assert rec.period_type is PeriodType.ANNUAL


class TestInstrumentMeta:
    def test_alias_lookup(self):
        meta = InstrumentMeta(
            symbol="KRX:005930",
            name="Samsung Electronics",
            asset_class=AssetClass.EQUITY,
            currency=Currency.KRW,
            aliases={SourceId.YFINANCE: "005930.KS", SourceId.PYKRX: "005930"},
            country="KR",
            exchange="KRX",
        )
        assert meta.alias_for(SourceId.YFINANCE) == "005930.KS"
        assert meta.alias_for(SourceId.OECD) is None


class TestProtocolConformance:
    def test_source_protocol_structural(self):
        class DummySource:
            source_id = SourceId.MANUAL

            def fetch(self, symbols, start, end):
                return symbols

            def to_standard(self, raw) -> list[StandardRecord]:
                return []

        assert isinstance(DummySource(), Source)

    def test_emitter_protocol_structural(self):
        class ListEmitter:
            def emit(self, records):
                return list(records)

        assert isinstance(ListEmitter(), Emitter)

    def test_non_conforming_rejected(self):
        class NotASource:
            pass

        assert not isinstance(NotASource(), Source)
