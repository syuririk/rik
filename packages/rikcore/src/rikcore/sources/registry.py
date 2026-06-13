"""Source registry — discovery and lookup of source adapters by id."""

from __future__ import annotations

from rikschema import SourceId
from rikschema.interfaces import Source


class SourceRegistry:
    """Holds source adapters keyed by SourceId."""

    def __init__(self) -> None:
        self._sources: dict[SourceId, Source] = {}

    def register(self, source: Source) -> None:
        self._sources[source.source_id] = source

    def get(self, source_id: SourceId) -> Source:
        if source_id not in self._sources:
            raise KeyError(f"no source registered for {source_id.value!r}")
        return self._sources[source_id]

    def all(self) -> list[Source]:
        return list(self._sources.values())

    def __contains__(self, source_id: SourceId) -> bool:
        return source_id in self._sources
