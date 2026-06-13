"""Optional base class for source adapters.

The contract (rikschema.interfaces.Source) is a Protocol, so adapters need
not inherit anything. This base just removes boilerplate (holding the
resolver, exposing source_id) for adapters that want it.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from rikschema import SourceId, StandardRecord

from rikcore.normalize import SymbolResolver


class SourceAdapter:
    """Convenience base; satisfies the Source protocol structurally."""

    source_id: SourceId

    def __init__(self, resolver: SymbolResolver) -> None:
        self.resolver = resolver

    def fetch(self, symbols: list[str], start: date, end: date) -> Any:  # pragma: no cover
        raise NotImplementedError

    def to_standard(self, raw: Any) -> list[StandardRecord]:  # pragma: no cover
        raise NotImplementedError
