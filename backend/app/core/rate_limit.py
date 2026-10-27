"""Simple in-memory rate limiter (per-key token bucket).

Suitable for a single process. In multi-instance production, back this with Redis.
"""
from __future__ import annotations

import time
from collections import defaultdict

from app.core.errors import RateLimitError

_buckets: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(key: str, *, limit: int, window_seconds: int) -> None:
    now = time.monotonic()
    window_start = now - window_seconds
    hits = _buckets[key]
    while hits and hits[0] < window_start:
        hits.pop(0)
    if len(hits) >= limit:
        raise RateLimitError("Too many requests. Please slow down and try again shortly.")
    hits.append(now)


def reset_rate_limits() -> None:
    _buckets.clear()
