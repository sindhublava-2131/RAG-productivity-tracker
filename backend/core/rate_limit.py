"""Dependency-free, in-process sliding-window rate limiter for FastAPI routes.

The limiter is keyed by client IP and is suitable for single-process uvicorn
deployments (the current architecture). It is deliberately dependency-free —
no Redis or third-party library required.

Usage:

    @router.post("/login")
    def login_user(..., _: None = Depends(rate_limit("auth-login"))):
        ...

The ``bucket`` name separates different routes; the optional ``limit`` /
``window_seconds`` override the defaults from settings.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

from core.config import settings

# bucket_key -> sliding window hits (monotonic timestamps)
_buckets: dict[str, deque[float]] = defaultdict(deque)
_lock = threading.Lock()


def _now() -> float:
    return time.monotonic()


def _prune(bucket_key: str, window_seconds: float) -> None:
    """Drop hits older than the window for a bucket key."""
    hits = _buckets[bucket_key]
    cutoff = _now() - window_seconds
    while hits and hits[0] <= cutoff:
        hits.popleft()


def is_allowed(bucket_key: str, limit: int, window_seconds: float) -> bool:
    """Return True if a new hit is allowed, recording it; thread-safe."""
    with _lock:
        _prune(bucket_key, window_seconds)
        if len(_buckets[bucket_key]) >= limit:
            return False
        _buckets[bucket_key].append(_now())
        return True


def remaining(bucket_key: str, limit: int, window_seconds: float) -> int:
    """Return how many hits remain in the window for this key (for headers)."""
    with _lock:
        _prune(bucket_key, window_seconds)
        return max(0, limit - len(_buckets[bucket_key]))


def rate_limit(
    bucket: str,
    *,
    limit: int | None = None,
    window_seconds: float = 60.0,
):
    """FastAPI dependency that rejects requests beyond the rate limit (429).

    Disabled automatically in testing mode (``APP_ENV=test``) so the offline
    test suite is unaffected.
    """

    def dependency(request: Request) -> None:
        if settings.is_testing or not settings.RATE_LIMIT_ENABLED:
            return
        effective_limit = limit
        if effective_limit is None:
            effective_limit = settings.RATE_LIMIT_GENERAL_PER_MINUTE
        client = request.client
        key = f"{bucket}:{client.host if client else 'unknown'}"
        if not is_allowed(key, effective_limit, window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please slow down and try again later.",
            )

    return dependency


def reset_limits() -> None:
    """Clear all recorded hits (used by tests)."""
    with _lock:
        _buckets.clear()


__all__ = ["rate_limit", "is_allowed", "remaining", "reset_limits"]
