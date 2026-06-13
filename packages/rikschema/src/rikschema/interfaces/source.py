"""The source-adapter contract.

A `Source` fetches raw data from one origin and converts it to standard
records. The two-method split (fetch / to_standard) is deliberate:

  * `fetch`       returns the source's raw payload, untouched. Cacheable and
                  debuggable in its native form.
  * `to_standard` is the pure transform raw -> list[StandardRecord]. No I/O,
                  so it's trivially unit-testable with recorded fixtures.

Defined as a `Protocol` (structural typing): rikcore adapters satisfy it by
shape, without importing or subclassing anything from rikschema beyond the
records they emit. That keeps the dependency arrow clean.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Protocol, runtime_checkable

from rikschema.enums import SourceId
from rikschema.records import StandardRecord


@runtime_checkable
class Source(Protocol):
    """Structural contract every rikcore source adapter fulfils."""

    source_id: SourceId

    def fetch(
        self,
        symbols: list[str],
        start: date,
        end: date,
    ) -> Any:
        """Fetch raw data for `symbols` over [start, end].

        `symbols` are canonical ids; the adapter is responsible for mapping
        them to its native tickers via the symbol resolver before the remote
        call. Returns the source's raw payload (shape is source-specific).

        Raises:
            FetchError: on network / API / rate-limit failure.
        """
        ...

    def to_standard(self, raw: Any) -> list[StandardRecord]:
        """Convert a raw payload from `fetch` into standard records.

        Pure function: no network access. Should raise NormalizationError
        for data it cannot faithfully map.
        """
        ...
