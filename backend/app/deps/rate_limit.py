"""In-memory rate limiter (per-session hourly quota).

Moved from ``backend/app/middleware/`` to ``backend/app/deps/``
because it is a plain function called imperatively, not an ASGI middleware.
Uses a module-level dict keyed by user id.  Suitable for single-process,
low-concurrency deployments.

**Limitation**: In-memory storage is NOT shared across worker processes
or server restarts.  For multi-worker deployments, replace with Redis-backed
storage (e.g. ``redis-py`` + ``cachetools``).
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, status

from configs.settings import settings

_hourly_buckets: dict[str, list[float]] = defaultdict(list)

# Login rate limit: 5 attempts per minute per IP
_LOGIN_BUCKETS: dict[str, list[float]] = defaultdict(list)
_LOGIN_MAX_PER_MINUTE = 5
_LOGIN_WINDOW = 60  # seconds


def check_rate_limit(user_id: str = "default") -> None:
    """Raise 429 if the user has exhausted hourly quota."""
    now = time.time()
    cutoff = now - 3600
    bucket = _hourly_buckets[user_id]
    bucket[:] = [t for t in bucket if t > cutoff]

    # Prune expired entries before checking (M11: prune before append, not after)
    if len(bucket) >= settings.session_hourly_quota:
        remaining = int(3600 - (now - min(bucket)))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"本小时提问次数已达上限（{settings.session_hourly_quota} 次），"
                f"约 {max(1, remaining // 60)} 分钟后重置，请稍后再试。"
            ),
        )
    bucket.append(now)

    # Prune empty buckets to prevent unbounded dict growth
    if not bucket:
        del _hourly_buckets[user_id]


def check_login_rate_limit(client_ip: str = "unknown") -> None:
    """Raise 429 if the IP has made too many login attempts.

    Stricter than the chat rate limit: 5 attempts per minute per IP.
    This prevents brute-force attacks on the access code.
    """
    now = time.time()
    cutoff = now - _LOGIN_WINDOW
    bucket = _LOGIN_BUCKETS[client_ip]
    bucket[:] = [t for t in bucket if t > cutoff]

    if len(bucket) >= _LOGIN_MAX_PER_MINUTE:
        remaining = int(_LOGIN_WINDOW - (now - min(bucket)))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"登录尝试过于频繁，请 {max(1, remaining)} 秒后重试"
            ),
        )
    bucket.append(now)

    # Prune empty buckets
    if not bucket:
        del _LOGIN_BUCKETS[client_ip]