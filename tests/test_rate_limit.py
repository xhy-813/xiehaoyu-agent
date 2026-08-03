"""Unit tests for backend/app/deps/rate_limit.py — IP quota + global daily cap."""

import os
os.environ["SKIP_CONFIG_VALIDATION"] = "1"

import time

import pytest
from fastapi import HTTPException

from backend.app.deps.rate_limit import (
    check_rate_limit,
    check_global_daily_cap,
    get_client_ip,
    _hourly_buckets,
    _daily_state,
)
import configs.settings as cfg


@pytest.fixture(autouse=True)
def _clean_state():
    _hourly_buckets.clear()
    _daily_state["date"] = ""
    _daily_state["count"] = 0
    yield
    _hourly_buckets.clear()
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
    def test_prefers_x_forwarded_for_first_hop(self):
        from fastapi import Request
        scope = {
            "type": "http", "method": "POST", "path": "/api/chat",
            "headers": [(b"x-forwarded-for", b"9.9.9.9, 10.0.0.1")],
            "client": ("127.0.0.1", 8000), "server": ("test", 80),
            "scheme": "http", "query_string": b"",
        }
        assert get_client_ip(Request(scope)) == "9.9.9.9"

    def test_falls_back_to_client_host(self):
        from fastapi import Request
        scope = {
            "type": "http", "method": "POST", "path": "/api/chat",
            "headers": [], "client": ("8.8.8.8", 8000),
            "server": ("test", 80), "scheme": "http", "query_string": b"",
        }
        assert get_client_ip(Request(scope)) == "8.8.8.8"