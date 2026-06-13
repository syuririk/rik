"""The orchestrator: fetch -> normalize -> validate -> emit.

Pulls a set of canonical symbols from one or more registered sources,
converts everything to standard records, validates the merged batch, and
hands it to an emitter. This is rikcore's top-level entry point and the
boundary that rikfeed consumes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from rikschema import SourceId, StandardRecord
from rikschema.interfaces import Emitter

from rikcore.emit import RecordsEmitter
from rikcore.sources import SourceRegistry
from rikcore.validate import ValidationReport, validate_batch


@dataclass
class PipelineResult:
    records: list[StandardRecord]
    report: ValidationReport
    output: Any  # whatever the emitter returned


class Orchestrator:
    """Coordinates sources, validation, and emission."""

    def __init__(
        self,
        registry: SourceRegistry,
        emitter: Emitter | None = None,
        *,
        strict: bool = False,
    ) -> None:
        self.registry = registry
        self.emitter = emitter or RecordsEmitter()
        self.strict = strict

    def run(
        self,
        symbols: list[str],
        start: date,
        end: date,
        sources: list[SourceId] | None = None,
    ) -> PipelineResult:
        """Run the full pipeline for `symbols` over [start, end].

        If `sources` is None, every registered source is queried and results
        are merged. Each source only fetches the symbols it can serve.
        """
        target_sources = (
            [self.registry.get(s) for s in sources]
            if sources is not None
            else self.registry.all()
        )

        merged: list[StandardRecord] = []
        for source in target_sources:
            # Only ask a source for symbols it can actually serve. Without this
            # a source receives canonical ids it has no alias for (e.g. an
            # index symbol going to a KR-equities-only source) and the resolver
            # raises SymbolResolutionError. A source exposing a `resolver` is
            # filtered via filter_supported; one without is passed all symbols.
            servable = self._servable_symbols(source, symbols)
            if not servable:
                continue
            raw = source.fetch(servable, start, end)
            records = source.to_standard(raw)
            merged.extend(records)

        report = validate_batch(merged)
        if self.strict and not report.ok:
            from rikschema import ValidationFailure

            raise ValidationFailure(report.summary())

        output = self.emitter.emit(merged)
        return PipelineResult(records=merged, report=report, output=output)

    @staticmethod
    def _servable_symbols(source: object, symbols: list[str]) -> list[str]:
        """Subset of `symbols` a source can serve.

        Source adapters built on SourceAdapter carry a `resolver`, which knows
        which symbols have an alias for that source. If a source exposes no
        resolver, we can't filter and pass everything through unchanged.
        """
        resolver = getattr(source, "resolver", None)
        source_id = getattr(source, "source_id", None)
        if resolver is None or source_id is None:
            return symbols
        return resolver.filter_supported(symbols, source_id)
