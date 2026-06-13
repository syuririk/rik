"""The emitter contract — rikcore's output boundary toward rikfeed.

An `Emitter` receives standard records and hands them off in whatever form a
consumer wants (a DataFrame, a record stream, a write to storage). rikcore
ships concrete emitters; rikfeed can also implement its own and pass it in.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from rikschema.records import StandardRecord


@runtime_checkable
class Emitter(Protocol):
    """Structural contract for anything that consumes standard records."""

    def emit(self, records: list[StandardRecord]) -> Any:
        """Consume a batch of standard records.

        Return value is emitter-specific: a DataFrame emitter returns a
        DataFrame, a storage emitter might return write counts, etc.
        """
        ...
