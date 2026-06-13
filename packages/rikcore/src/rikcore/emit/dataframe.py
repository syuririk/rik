"""Emitters: rikcore's output boundary toward rikfeed.

Each emitter satisfies rikschema.interfaces.Emitter. RecordsEmitter is the
trivial pass-through; DataFrameEmitter widens records into a tabular form for
analysis (the cross-sectional regression use case).
"""

from __future__ import annotations

from typing import Any

from rikschema import StandardRecord


class RecordsEmitter:
    """Returns the records unchanged (the canonical stream form)."""

    def emit(self, records: list[StandardRecord]) -> list[StandardRecord]:
        return records


class DictEmitter:
    """Returns records as a list of plain dicts (JSON-ready)."""

    def emit(self, records: list[StandardRecord]) -> list[dict[str, Any]]:
        return [r.model_dump(mode="json") for r in records]


class DataFrameEmitter:
    """Returns a pandas DataFrame. Imports pandas lazily."""

    def emit(self, records: list[StandardRecord]) -> Any:
        import pandas as pd

        if not records:
            return pd.DataFrame()
        rows = [r.model_dump(mode="json") for r in records]
        df = pd.DataFrame(rows)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values(["symbol", "timestamp"]).reset_index(drop=True)
        return df
