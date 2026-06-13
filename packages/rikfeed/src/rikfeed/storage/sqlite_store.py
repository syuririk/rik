"""SQLite (WAL) storage for standard records.

rikfeed's persistence layer. Uses WAL mode for concurrent read during the
post-KRX-close write. Schema mirrors the OHLCV standard record; other record
types can get their own tables as the feed grows.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path

from rikschema import OHLCVRecord, StandardRecord

_SCHEMA = """
CREATE TABLE IF NOT EXISTS ohlcv (
    symbol      TEXT    NOT NULL,
    timestamp   TEXT    NOT NULL,
    source      TEXT    NOT NULL,
    asset_class TEXT    NOT NULL,
    open        REAL    NOT NULL,
    high        REAL    NOT NULL,
    low         REAL    NOT NULL,
    close       REAL    NOT NULL,
    volume      REAL    NOT NULL,
    currency    TEXT    NOT NULL,
    adjusted    INTEGER NOT NULL,
    PRIMARY KEY (symbol, timestamp, source)
);
"""


class SQLiteStore:
    """Append/upsert standard OHLCV records into a WAL-mode SQLite db."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def write(self, records: Iterable[StandardRecord]) -> int:
        """Upsert OHLCV records. Returns count written. Non-OHLCV ignored."""
        rows = [
            (
                r.symbol,
                r.timestamp.isoformat(),
                r.source.value,
                r.asset_class.value,
                r.open,
                r.high,
                r.low,
                r.close,
                r.volume,
                r.currency.value,
                int(r.adjusted),
            )
            for r in records
            if isinstance(r, OHLCVRecord)
        ]
        if not rows:
            return 0
        self._conn.executemany(
            """
            INSERT INTO ohlcv
                (symbol, timestamp, source, asset_class,
                 open, high, low, close, volume, currency, adjusted)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(symbol, timestamp, source) DO UPDATE SET
                open=excluded.open, high=excluded.high, low=excluded.low,
                close=excluded.close, volume=excluded.volume,
                currency=excluded.currency, adjusted=excluded.adjusted
            """,
            rows,
        )
        self._conn.commit()
        return len(rows)

    def count(self) -> int:
        cur = self._conn.execute("SELECT COUNT(*) FROM ohlcv")
        return int(cur.fetchone()[0])

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "SQLiteStore":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
