"""Generic field-name mapping helper.

Each source has its own column names (yfinance: 'Open'/'Close', pykrx:
'시가'/'종가'). A FieldMapper centralizes the rename so adapters stay
declarative.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class FieldMapper:
    """Renames keys in a record dict according to a fixed mapping."""

    def __init__(self, mapping: Mapping[str, str]) -> None:
        # source_field -> standard_field
        self._mapping = dict(mapping)

    def apply(self, row: Mapping[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for src_key, std_key in self._mapping.items():
            if src_key in row:
                out[std_key] = row[src_key]
        return out

    def missing(self, row: Mapping[str, Any]) -> list[str]:
        """Source fields expected by the mapping but absent in `row`."""
        return [k for k in self._mapping if k not in row]
