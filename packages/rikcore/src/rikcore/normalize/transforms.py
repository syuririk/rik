"""Explicit value transforms (currency, scale).

These are deliberately *opt-in*: standard records store values in their
native form, and any conversion is an explicit pipeline step. This keeps the
raw record faithful to its source and makes conversions auditable.
"""

from __future__ import annotations

from rikschema import Currency, OHLCVRecord


def convert_ohlcv_currency(
    record: OHLCVRecord,
    rate: float,
    target: Currency,
) -> OHLCVRecord:
    """Return a new OHLCVRecord with prices multiplied by `rate`.

    `rate` is target-per-native (e.g. native KRW, target USD -> rate ~1/1350).
    Volume is unchanged. Produces a new frozen record.
    """
    if rate <= 0:
        raise ValueError("rate must be positive")
    return record.model_copy(
        update={
            "open": record.open * rate,
            "high": record.high * rate,
            "low": record.low * rate,
            "close": record.close * rate,
            "currency": target,
        }
    )
