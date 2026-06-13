"""Canonical symbol resolution across sources.

The resolver holds a registry of InstrumentMeta and translates in both
directions:

  canonical id  <->  a given source's native ticker

This is what lets one pipeline ask several sources for the "same" instrument
and merge the results: every source adapter resolves its native tickers
through here before fetching, and stamps the canonical id on the records it
emits.
"""

from __future__ import annotations

from collections.abc import Iterable

from rikschema import InstrumentMeta, SourceId, SymbolResolutionError


class SymbolResolver:
    """Bidirectional map between canonical ids and source-native tickers."""

    def __init__(self, instruments: Iterable[InstrumentMeta] = ()) -> None:
        self._by_symbol: dict[str, InstrumentMeta] = {}
        # (source, native_ticker) -> canonical symbol
        self._alias_index: dict[tuple[SourceId, str], str] = {}
        for meta in instruments:
            self.register(meta)

    def register(self, meta: InstrumentMeta) -> None:
        self._by_symbol[meta.symbol] = meta
        for source, native in meta.aliases.items():
            self._alias_index[(source, native)] = meta.symbol

    def to_native(self, symbol: str, source: SourceId) -> str:
        """Canonical id -> that source's native ticker."""
        meta = self._by_symbol.get(symbol)
        if meta is None:
            raise SymbolResolutionError(f"unknown canonical symbol {symbol!r}")
        native = meta.alias_for(source)
        if native is None:
            raise SymbolResolutionError(
                f"{symbol!r} has no alias for source {source.value!r}"
            )
        return native

    def to_canonical(self, native: str, source: SourceId) -> str:
        """A source's native ticker -> canonical id."""
        symbol = self._alias_index.get((source, native))
        if symbol is None:
            raise SymbolResolutionError(
                f"native ticker {native!r} from {source.value!r} is unmapped"
            )
        return symbol

    def meta(self, symbol: str) -> InstrumentMeta:
        meta = self._by_symbol.get(symbol)
        if meta is None:
            raise SymbolResolutionError(f"unknown canonical symbol {symbol!r}")
        return meta

    def known_symbols(self) -> list[str]:
        return list(self._by_symbol)

    def filter_supported(
        self, symbols: Iterable[str], source: SourceId
    ) -> list[str]:
        """Subset of `symbols` that `source` can actually serve."""
        out = []
        for s in symbols:
            meta = self._by_symbol.get(s)
            if meta is not None and meta.alias_for(source) is not None:
                out.append(s)
        return out
