"""rikfeed — persistence & scheduling consumer of standardized rik data.

Consumes rikschema standard records (produced by rikcore), persists them to a
WAL-mode SQLite store, and computes feed run timing relative to the KRX close.
"""

from __future__ import annotations

from rikfeed.schedule import next_run_after
from rikfeed.storage import SQLiteStore, StoreEmitter

__version__ = "0.1.0"

__all__ = ["__version__", "SQLiteStore", "StoreEmitter", "next_run_after"]
