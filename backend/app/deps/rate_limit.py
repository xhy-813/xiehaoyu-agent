"""In-memory rate limiter (per-IP hourly quota + site-wide daily cap).

Keyed by client IP.  Suitable for single-process, low-concurrency deployments.

**Limitation**: In-memory storage is NOT shared across worker processes
or server restarts.  For multi-worker deployments, replace with Redis-backed
storage (e.g. ``redis-py`` + ``cachetools``).
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

from configs.settings import settings

_hourly_buckets: dict[str, list[float]] = defaultdict(list)

# Site-wide daily cap state: {"date": "YYYY-MM-DD", "count": int}
_daily_state: dict[str, object] = {"date": "", "count": 0}


def get_client_ip(request: Request) -> str:
    """Extract the real client IP, honoring X-Forwarded-For from Nginx."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(client_ip: str = "unknown") -> None:
    """Raise 429 if this IP has exhausted its hourly quota."""
    now = time.time()
    cutoff = now - 3600
    bucket = _hourly_buckets[client_ip]
    bucket[:] = [t for t in bucket if t > cutoff]

    # Prune expired entries before checking (M11: prune before append, not after)
    if len(bucket) >= settings.ip_hourly_quota:
        remaining = int(3600 - (now - min(bucket)))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"本小时提问次数已达上限（{settings.ip_hourly_quota} 次），"
                f"约 {max(1, remaining // 60)} 分钟后重置，请稍后再试。"
            ),
        )
    bucket.append(now)


def check_global_daily_cap() -> None:
    """Raise 429 if the site-wide daily quota is exhausted (anti-abuse backstop)."""
    today = time.strftime("%Y-%m-%d")
    if _daily_state["date"] != today:
        _daily_state["date"] = today
        _daily_state["count"] = 0

    if _daily_state["count"] >= settings.global_daily_quota:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="今日体验名额已用完，欢迎明天再来，或通过页脚联系方式找我。",
        )
    _daily_state["count"] += 1
