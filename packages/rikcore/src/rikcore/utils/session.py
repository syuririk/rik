"""Shared requests.Session factory for TCP connection reuse.

Reusing a Session across many small HTTP calls avoids per-request connection
setup overhead — a pattern proven out in dart-report-reader.
"""

from __future__ import annotations

from typing import Any


def build_session(
    *,
    total_retries: int = 3,
    backoff_factor: float = 0.3,
    pool_maxsize: int = 16,
) -> Any:
    """Create a requests.Session with retry + connection pooling. Lazy import."""
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    session = requests.Session()
    retry = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
    )
    adapter = HTTPAdapter(max_retries=retry, pool_maxsize=pool_maxsize)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session
