"""Configuration loading.

`defaults.yaml` is the canonical config source (the pattern carried over from
Study Assistant). Loading is lazy on PyYAML.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_DEFAULTS = Path(__file__).parent / "defaults.yaml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML config, falling back to packaged defaults."""
    import yaml

    target = Path(path) if path else _DEFAULTS
    with target.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


__all__ = ["load_config"]
