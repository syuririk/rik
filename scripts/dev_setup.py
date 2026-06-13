#!/usr/bin/env python3
"""Editable-install all workspace packages without uv.

Installs in dependency order: rikschema -> rikcore -> rikfeed.
Prefer `uv sync` if you have uv; this is the pip fallback.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = ["rikschema", "rikcore", "rikfeed"]


def main() -> int:
    for name in PACKAGES:
        pkg = ROOT / "packages" / name
        print(f"==> pip install -e {pkg}")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(pkg)],
            check=False,
        )
        if result.returncode != 0:
            print(f"FAILED installing {name}", file=sys.stderr)
            return result.returncode
    print("\nAll packages installed editable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
