"""The base class for every standard record in the rik ecosystem.

`StandardRecord` encodes the normalization invariants that rikcore guarantees
and rikfeed relies on:

  * `symbol`     — canonical instrument id (resolved by rikcore, NOT the raw
                   source ticker). e.g. "KRX:005930", "INDEX:KOSPI".
  * `timestamp`  — timezone-aware, normalized to KST. Naive datetimes are
                   rejected so an ambiguous time can never enter the pipeline.
  * `source`     — provenance, for dedup / priority across overlapping feeds.
  * `asset_class`— coarse classification.

Subclasses add their own payload fields (OHLCV, fundamentals, ...).
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, field_validator

from rikschema.enums import AssetClass, SourceId

KST = ZoneInfo("Asia/Seoul")


class StandardRecord(BaseModel):
    """Base for all standardized records.

    `extra="forbid"` ensures a typo'd or unexpected field fails loudly at
    construction rather than silently passing downstream.
    """

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,            # records are immutable once normalized
        use_enum_values=False,  # keep enum instances, not raw strings
    )

    symbol: str
    timestamp: datetime
    source: SourceId
    asset_class: AssetClass

    @field_validator("timestamp")
    @classmethod
    def _ensure_kst_aware(cls, v: datetime) -> datetime:
        """Reject naive datetimes; convert any aware datetime to KST."""
        if v.tzinfo is None:
            raise ValueError(
                "timestamp must be timezone-aware; "
                "normalize at the source adapter before constructing a record"
            )
        return v.astimezone(KST)

    @field_validator("symbol")
    @classmethod
    def _non_empty_symbol(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("symbol must be a non-empty canonical id")
        return v
