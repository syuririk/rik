"""Storage backends. SQLiteStore doubles as a rikschema Emitter."""

from __future__ import annotations

from rikschema import StandardRecord

from rikfeed.storage.sqlite_store import SQLiteStore


class StoreEmitter:
    """Adapts a SQLiteStore to the rikschema.Emitter protocol.

    Lets rikcore's Orchestrator write straight to the feed's store:
        Orchestrator(registry, emitter=StoreEmitter(store)).run(...)
    """

    def __init__(self, store: SQLiteStore) -> None:
        self._store = store

    def emit(self, records: list[StandardRecord]) -> int:
        return self._store.write(records)


__all__ = ["SQLiteStore", "StoreEmitter"]
