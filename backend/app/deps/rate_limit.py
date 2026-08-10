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

# 会话写操作的独立限流桶（808 审查 M11：/api/sessions 此前无任何限流，
# 攻击者可用随机 X-User-Id 无限创建会话撑库）
_sessions_buckets: dict[str, list[float]] = defaultdict(list)

# Site-wide daily cap state: {"date": "YYYY-MM-DD", "count": int}
_daily_state: dict[str, object] = {"date": "", "count": 0}


def get_client_ip(request: Request) -> str:
    """Return the real client IP for rate limiting.

    生产环境 uvicorn 以 ``--proxy-headers`` 运行，其 ProxyHeadersMiddleware
    已把 ``request.client.host`` 解析为 X-Forwarded-For 的**最右跳**
    （即 Nginx 看到的真实对端）。不要自行解析 XFF 头：Nginx 的
    ``$proxy_add_x_forwarded_for`` 是追加语义，第一跳由客户端控制、可任意
    伪造（808 审查 H2——此前取第一跳导致按 IP 限流可被绕过）。
    """
    return request.client.host if request.client else "unknown"


def check_rate_limit(client_ip: str = "unknown") -> None:
    """Raise 429 if this IP has exhausted its hourly quota."""
    now = time.time()
    cutoff = now - 3600
    bucket = _hourly_buckets[client_ip]
    bucket[:] = [t for t in bucket if t > cutoff]
    if not bucket:
        # 全部过期：先删除再经 defaultdict 重建，避免字典随唯一 IP 数无界增长
        del _hourly_buckets[client_ip]
        bucket = _hourly_buckets[client_ip]

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


def check_sessions_write_limit(client_ip: str, quota: int | None = None) -> None:
    """会话写端点（创建/改名/删除）的按 IP 小时限流。

    与聊天配额独立（会话操作不消耗 LLM 额度，额度更宽）；
    ``quota`` 可由测试注入，默认取 ``settings.sessions_ip_hourly_quota``。
    """
    limit = quota if quota is not None else settings.sessions_ip_hourly_quota
    now = time.time()
    cutoff = now - 3600
    bucket = _sessions_buckets[client_ip]
    bucket[:] = [t for t in bucket if t > cutoff]
    if not bucket:
        del _sessions_buckets[client_ip]
        bucket = _sessions_buckets[client_ip]
    if len(bucket) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="会话操作过于频繁，请稍后再试。",
        )
    bucket.append(now)
