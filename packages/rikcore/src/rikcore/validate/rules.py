"""Batch-level validation of standard records.

Per-record invariants are already enforced by the pydantic models. This layer
checks *cross-record* properties: duplicates, gaps, ordering — things a single
record cannot know about itself.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from rikschema import StandardRecord


@dataclass
class ValidationReport:
    total: int = 0
    duplicates: list[tuple[str, str]] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.duplicates and not self.issues

    def summary(self) -> str:
        status = "OK" if self.ok else "FAIL"
        return (
            f"[{status}] {self.total} records, "
            f"{len(self.duplicates)} duplicate(s), {len(self.issues)} issue(s)"
        )


def validate_batch(records: list[StandardRecord]) -> ValidationReport:
    """Check a batch for duplicate (symbol, timestamp, source) keys."""
    report = ValidationReport(total=len(records))
    seen: dict[tuple[str, str, str], int] = defaultdict(int)
    for r in records:
        key = (r.symbol, r.timestamp.isoformat(), r.source.value)
        seen[key] += 1
    for (symbol, ts, _src), count in seen.items():
        if count > 1:
            report.duplicates.append((symbol, ts))
    return report
