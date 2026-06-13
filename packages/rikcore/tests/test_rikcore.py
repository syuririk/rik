"""Tests for rikcore: resolver, manual source, validation, pipeline."""

from __future__ import annotations

from datetime import date

import pytest

from rikschema import (
    AssetClass,
    Currency,
    InstrumentMeta,
    SourceId,
    SymbolResolutionError,
)

from rikcore import (
    DictEmitter,
    ManualSource,
    Orchestrator,
    RecordsEmitter,
    SourceRegistry,
    SymbolResolver,
    validate_batch,
)

SAMSUNG = InstrumentMeta(
    symbol="KRX:005930",
    name="Samsung Electronics",
    asset_class=AssetClass.EQUITY,
    currency=Currency.KRW,
    aliases={SourceId.YFINANCE: "005930.KS", SourceId.FDR: "005930"},
    country="KR",
    exchange="KRX",
)


def _resolver() -> SymbolResolver:
    return SymbolResolver([SAMSUNG])


def _rows():
    return [
        {
            "symbol": "KRX:005930", "day": date(2025, 1, 2),
            "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0,
            "volume": 1000.0, "currency": Currency.KRW,
            "asset_class": AssetClass.EQUITY,
        },
        {
            "symbol": "KRX:005930", "day": date(2025, 1, 3),
            "open": 105.0, "high": 112.0, "low": 104.0, "close": 108.0,
            "volume": 1200.0, "currency": Currency.KRW,
            "asset_class": AssetClass.EQUITY,
        },
    ]


class TestSymbolResolver:
    def test_to_native(self):
        r = _resolver()
        assert r.to_native("KRX:005930", SourceId.YFINANCE) == "005930.KS"
        assert r.to_native("KRX:005930", SourceId.FDR) == "005930"

    def test_to_canonical(self):
        r = _resolver()
        assert r.to_canonical("005930.KS", SourceId.YFINANCE) == "KRX:005930"

    def test_unknown_symbol_raises(self):
        with pytest.raises(SymbolResolutionError):
            _resolver().to_native("KRX:000000", SourceId.FDR)

    def test_no_alias_for_source_raises(self):
        with pytest.raises(SymbolResolutionError):
            _resolver().to_native("KRX:005930", SourceId.OECD)

    def test_filter_supported(self):
        r = _resolver()
        got = r.filter_supported(["KRX:005930", "KRX:000000"], SourceId.FDR)
        assert got == ["KRX:005930"]


class TestManualSource:
    def test_fetch_filters_by_window(self):
        src = ManualSource(_resolver(), _rows())
        raw = src.fetch(["KRX:005930"], date(2025, 1, 2), date(2025, 1, 2))
        assert len(raw) == 1

    def test_to_standard(self):
        src = ManualSource(_resolver(), _rows())
        raw = src.fetch(["KRX:005930"], date(2025, 1, 1), date(2025, 1, 31))
        records = src.to_standard(raw)
        assert len(records) == 2
        assert records[0].symbol == "KRX:005930"
        assert records[0].timestamp.tzinfo is not None


class TestValidation:
    def test_clean_batch_ok(self):
        src = ManualSource(_resolver(), _rows())
        records = src.to_standard(
            src.fetch(["KRX:005930"], date(2025, 1, 1), date(2025, 1, 31))
        )
        assert validate_batch(records).ok

    def test_duplicate_detected(self):
        src = ManualSource(_resolver(), _rows() + _rows()[:1])
        records = src.to_standard(
            src.fetch(["KRX:005930"], date(2025, 1, 1), date(2025, 1, 31))
        )
        report = validate_batch(records)
        assert not report.ok
        assert report.duplicates


class TestPipeline:
    def test_end_to_end_records(self):
        registry = SourceRegistry()
        registry.register(ManualSource(_resolver(), _rows()))
        orch = Orchestrator(registry, RecordsEmitter())
        result = orch.run(["KRX:005930"], date(2025, 1, 1), date(2025, 1, 31))
        assert len(result.records) == 2
        assert result.report.ok
        assert result.output == result.records

    def test_dict_emitter(self):
        registry = SourceRegistry()
        registry.register(ManualSource(_resolver(), _rows()))
        orch = Orchestrator(registry, DictEmitter())
        result = orch.run(["KRX:005930"], date(2025, 1, 1), date(2025, 1, 31))
        assert isinstance(result.output, list)
        assert result.output[0]["symbol"] == "KRX:005930"
