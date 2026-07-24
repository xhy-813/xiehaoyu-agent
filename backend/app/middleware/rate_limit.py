"""In-memory rate limiter (per-session hourly quota).

Migrated from ``ui/auth.py`` ``check_rate_limit()``.  Uses a module-level
dict keyed by user id ('' for anonymous).  Suitable for single-process,
low-concurrency deployments.
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, status

from configs.settings import settings

_hourly_buckets: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(user_id: str = "default") -> None:
    """Raise 429 if the user has exhausted hourly quota."""
    now = time.time()
    cutoff = now - 3600
    bucket = _hourly_buckets[user_id]
    bucket[:] = [t for t in bucket if t > cutoff]

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