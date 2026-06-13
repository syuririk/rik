"""Behavioral contracts (Protocols) implemented by rikcore, expected by rikfeed."""

from __future__ import annotations

from rikschema.interfaces.emitter import Emitter
from rikschema.interfaces.source import Source

__all__ = ["Source", "Emitter"]
