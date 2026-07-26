"""Unit tests for backend/app/middleware/rate_limit.py — quota enforcement."""

import os
os.environ["SKIP_CONFIG_VALIDATION"] = "1"

import time

import pytest
from fastapi import HTTPException

from backend.app.deps.rate_limit import check_rate_limit, _hourly_buckets


@pytest.fixture(autouse=True)
def _clean_buckets():
    """Reset the in-memory bucket dict before each test."""
    _hourly_buckets.clear()
    yield
    _hourly_buckets.clear()


class TestRateLimit:
    def test_first_request_does_not_raise(self):
        check_rate_limit("user-a")

    def test_requests_under_quota_do_not_raise(self):
        for _ in range(5):
            check_rate_limit("user-b")

    def test_exceeding_quota_raises_429(self):
        import configs.settings as cfg
        quota = cfg.settings.session_hourly_quota
        for _ in range(quota):
            check_rate_limit("user-c")
        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit("user-c")
        assert exc_info.value.status_code == 429

    def test_users_are_isolated(self):
        """User A using their quota should not affect User B."""
        import configs.settings as cfg
        quota = cfg.settings.session_hourly_quota
        # Exhaust user-a's quota
        for _ in range(quota):
            check_rate_limit("user-a")
        with pytest.raises(HTTPException):
            check_rate_limit("user-a")
        # User B should still be fine
        check_rate_limit("user-b")

    def test_different_user_ids_have_separate_buckets(self):
        check_rate_limit("alice")
        check_rate_limit("bob")
        # Each should have their own bucket
        assert "alice" in _hourly_buckets
        assert "bob" in _hourly_buckets
        assert len(_hourly_buckets["alice"]) == 1
        assert len(_hourly_buckets["bob"]) == 1

    def test_expired_entries_are_cleaned(self):
        """Entries older than 1 hour should be pruned from the bucket."""
        now = time.time()
        _hourly_buckets["user-d"] = [now - 3700, now - 100]  # one expired
        check_rate_limit("user-d")
        # Only the non-expired entry should remain + the new one
        assert len(_hourly_buckets["user-d"]) == 2