"""Unit tests for backend/app/deps/rate_limit.py — IP quota + global daily cap."""

import os
os.environ["SKIP_CONFIG_VALIDATION"] = "1"

import time

import pytest
from fastapi import HTTPException

from backend.app.deps.rate_limit import (
    check_rate_limit,
    check_global_daily_cap,
    check_sessions_write_limit,
    get_client_ip,
    _hourly_buckets,
    _sessions_buckets,
    _daily_state,
)
import configs.settings as cfg


@pytest.fixture(autouse=True)
def _clean_state():
    _hourly_buckets.clear()
    _sessions_buckets.clear()
    _daily_state["date"] = ""
    _daily_state["count"] = 0
    yield
    _hourly_buckets.clear()
    _sessions_buckets.clear()
    _daily_state["date"] = ""
    _daily_state["count"] = 0


class TestIpHourlyQuota:
    def test_first_request_does_not_raise(self):
        check_rate_limit("1.2.3.4")

    def test_exceeding_quota_raises_429(self):
        quota = cfg.settings.ip_hourly_quota
        for _ in range(quota):
            check_rate_limit("1.2.3.4")
        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit("1.2.3.4")
        assert exc_info.value.status_code == 429
        assert "本小时" in exc_info.value.detail

    def test_ips_are_isolated(self):
        quota = cfg.settings.ip_hourly_quota
        for _ in range(quota):
            check_rate_limit("1.1.1.1")
        with pytest.raises(HTTPException):
            check_rate_limit("1.1.1.1")
        check_rate_limit("2.2.2.2")  # 另一个 IP 不受影响

    def test_expired_entries_are_cleaned(self):
        now = time.time()
        _hourly_buckets["3.3.3.3"] = [now - 3700, now - 100]
        check_rate_limit("3.3.3.3")
        assert len(_hourly_buckets["3.3.3.3"]) == 2  # 过期 1 条被清 + 新增 1 条


class TestGlobalDailyCap:
    def test_under_cap_does_not_raise(self):
        check_global_daily_cap()
        assert _daily_state["count"] == 1

    def test_exceeding_cap_raises_429(self):
        _daily_state["date"] = time.strftime("%Y-%m-%d")
        _daily_state["count"] = cfg.settings.global_daily_quota
        with pytest.raises(HTTPException) as exc_info:
            check_global_daily_cap()
        assert exc_info.value.status_code == 429
        assert "今日体验名额已用完" in exc_info.value.detail

    def test_date_rollover_resets_count(self):
        _daily_state["date"] = "2000-01-01"
        _daily_state["count"] = cfg.settings.global_daily_quota
        check_global_daily_cap()  # 跨天后重置
        assert _daily_state["date"] == time.strftime("%Y-%m-%d")
        assert _daily_state["count"] == 1


class TestGetClientIp:
    def test_ignores_spoofable_xff_first_hop(self):
        """808 审查 H2：XFF 第一跳可被客户端伪造（Nginx 是追加语义而非覆盖），
        必须只信任 request.client.host——生产环境 uvicorn --proxy-headers
        会将其解析为 XFF 最右跳（即 Nginx 看到的真实对端）。"""
        from fastapi import Request
        scope = {
            "type": "http", "method": "POST", "path": "/api/chat",
            "headers": [(b"x-forwarded-for", b"9.9.9.9, 10.0.0.1")],
            "client": ("10.0.0.1", 8000), "server": ("test", 80),
            "scheme": "http", "query_string": b"",
        }
        # 伪造的第一跳 9.9.9.9 不得成为限流键
        assert get_client_ip(Request(scope)) == "10.0.0.1"

    def test_falls_back_to_client_host(self):
        from fastapi import Request
        scope = {
            "type": "http", "method": "POST", "path": "/api/chat",
            "headers": [], "client": ("8.8.8.8", 8000),
            "server": ("test", 80), "scheme": "http", "query_string": b"",
        }
        assert get_client_ip(Request(scope)) == "8.8.8.8"


class TestSessionsWriteLimit:
    """808 审查 M11：会话写端点的独立限流桶。"""

    def test_under_quota_passes(self):
        check_sessions_write_limit("9.9.9.9", quota=3)
        check_sessions_write_limit("9.9.9.9", quota=3)

    def test_over_quota_raises_429(self):
        for _ in range(3):
            check_sessions_write_limit("9.9.9.9", quota=3)
        with pytest.raises(HTTPException) as exc_info:
            check_sessions_write_limit("9.9.9.9", quota=3)
        assert exc_info.value.status_code == 429
        assert "会话操作" in exc_info.value.detail

    def test_independent_from_chat_bucket(self):
        """会话写桶与聊天桶互不影响。"""
        for _ in range(3):
            check_sessions_write_limit("7.7.7.7", quota=3)
        check_rate_limit("7.7.7.7")  # 聊天桶首次调用，不应受会话桶影响

    def test_ips_isolated(self):
        for _ in range(3):
            check_sessions_write_limit("5.5.5.5", quota=3)
        check_sessions_write_limit("6.6.6.6", quota=3)  # 另一个 IP 不受影响