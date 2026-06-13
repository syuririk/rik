"""Shared exception types for the rik ecosystem.

These live in rikschema (the contract package) so that producers (rikcore)
and consumers (rikfeed) raise and catch the *same* exception classes without
importing each other.
"""

from __future__ import annotations


class RikError(Exception):
    """Base class for all rik ecosystem errors."""


class SchemaError(RikError):
    """A record violated the standard schema contract."""


class SourceError(RikError):
    """A data source failed to fetch or produce data."""

    def __init__(self, message: str, *, source_id: str | None = None) -> None:
        self.source_id = source_id
        if source_id:
            message = f"[{source_id}] {message}"
        super().__init__(message)


class FetchError(SourceError):
    """Raised when a source's remote fetch fails (network, API, rate limit)."""


class NormalizationError(RikError):
    """Raised when raw source data cannot be mapped to a standard record."""

    def __init__(self, message: str, *, field: str | None = None) -> None:
        self.field = field
        if field:
            message = f"{message} (field={field!r})"
        super().__init__(message)


class SymbolResolutionError(NormalizationError):
    """Raised when a source symbol cannot be mapped to a canonical id."""


class ValidationFailure(RikError):
    """Raised when a batch of records fails validation rules."""
