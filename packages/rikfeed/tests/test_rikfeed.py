"""Tests for rikfeed: SQLite store, StoreEmitter, scheduler, and the full
rikcore -> rikfeed integration."""

from __future__ import annotations

from datetime import date, datetime

from rikschema import AssetClass, Currency, InstrumentMeta, SourceId

from rikcore import ManualSource, Orchestrator, SourceRegistry, SymbolResolver
from rikfeed import SQLiteStore, next_run_after
from rikfeed.storage import StoreEmitter
from rikfeed.schedule import KRX_CLOSE
from rikschema.records.base import KST

SAMSUNG = InstrumentMeta(
    symbol="KRX:005930",
    name="Samsung Electronics",
    asset_class=AssetClass.EQUITY,
    currency=Currency.KRW,
    aliases={SourceId.FDR: "005930"},
)


def _rows():
    return [
        {
            "symbol": "KRX:005930", "day": date(2025, 1, 2),
            "open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0,
            "volume": 1000.0, "currency": Currency.KRW,
            "asset_class": AssetClass.EQUITY,
        },
    ]


class TestSQLiteStore:
    def test_write_and_count(self, tmp_path):
        resolver = SymbolResolver([SAMSUNG])
        src = ManualSource(resolver, _rows())
        records = src.to_standard(
            src.fetch(["KRX:005930"], date(2025, 1, 1), date(2025, 1, 31))
        )
        with SQLiteStore(tmp_path / "feed.db") as store:
            written = store.write(records)
            assert written == 1
            assert store.count() == 1

    def test_upsert_idempotent(self, tmp_path):
        resolver = SymbolResolver([SAMSUNG])
        src = ManualSource(resolver, _rows())
        records = src.to_standard(
            src.fetch(["KRX:005930"], date(2025, 1, 1), date(2025, 1, 31))
        )
        with SQLiteStore(tmp_path / "feed.db") as store:
            store.write(records)
            store.write(records)  # same key -> upsert, not duplicate
            assert store.count() == 1


class TestIntegration:
    def test_orchestrator_writes_to_store(self, tmp_path):
        resolver = SymbolResolver([SAMSUNG])
        registry = SourceRegistry()
        registry.register(ManualSource(resolver, _rows()))

        with SQLiteStore(tmp_path / "feed.db") as store:
            orch = Orchestrator(registry, StoreEmitter(store))
            result = orch.run(["KRX:005930"], date(2025, 1, 1), date(2025, 1, 31))
            assert result.output == 1   # rows written by StoreEmitter
            assert store.count() == 1


class TestScheduler:
    def test_next_run_is_after_now(self):
        now = datetime(2025, 1, 2, 10, 0, tzinfo=KST)  # Thu morning
        nxt = next_run_after(now)
        assert nxt > now
        assert nxt.time() > KRX_CLOSE

    def test_weekend_rolls_to_monday(self):
        sat = datetime(2025, 1, 4, 18, 0, tzinfo=KST)  # Saturday evening
        nxt = next_run_after(sat)
        assert nxt.weekday() == 0  # Monday
