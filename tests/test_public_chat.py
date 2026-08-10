"""Tests for public /api/chat access (no JWT) + health endpoints.

`test_auth.py` was removed along with the login system; the health-check
tests live here now.
"""

import os
os.environ["SKIP_CONFIG_VALIDATION"] = "1"

import time

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.deps.rate_limit import _hourly_buckets, _daily_state
import configs.settings as cfg

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean_state():
    _hourly_buckets.clear()
    _daily_state["date"] = ""
    _daily_state["count"] = 0
    yield
    _hourly_buckets.clear()
    _daily_state["date"] = ""
    _daily_state["count"] = 0


def _fake_stream(question: str, history_text: str = ""):
    async def gen():
        yield {"type": "final_answer", "node": "finalize", "data": {"answer": "ok"}}
    return gen()


class TestPublicChat:
    def test_chat_requires_no_token(self, monkeypatch):
        monkeypatch.setattr("backend.app.routers.chat.stream_run", _fake_stream)
        resp = client.post("/api/chat", json={"question": "你好"})
        assert resp.status_code == 200
        assert "final_answer" in resp.text

    def test_chat_empty_question_returns_422(self):
        resp = client.post("/api/chat", json={"question": ""})
        assert resp.status_code == 422

    def test_login_route_removed(self):
        resp = client.post("/api/auth/login", json={"access_code": "whatever"})
        assert resp.status_code == 404

    def test_ip_hourly_quota_returns_429(self, monkeypatch):
        monkeypatch.setattr("backend.app.routers.chat.stream_run", _fake_stream)
        headers = {"x-forwarded-for": "203.0.113.7"}
        for _ in range(cfg.settings.ip_hourly_quota):
            resp = client.post("/api/chat", json={"question": "hi"}, headers=headers)
            assert resp.status_code == 200
        resp = client.post("/api/chat", json={"question": "hi"}, headers=headers)
        assert resp.status_code == 429
        assert "本小时" in resp.json()["detail"]

    def test_global_daily_cap_returns_429(self, monkeypatch):
        monkeypatch.setattr("backend.app.routers.chat.stream_run", _fake_stream)
        _daily_state["date"] = time.strftime("%Y-%m-%d")
        _daily_state["count"] = cfg.settings.global_daily_quota
        resp = client.post("/api/chat", json={"question": "hi"})
        assert resp.status_code == 429
        assert "今日体验名额已用完" in resp.json()["detail"]


class TestHealth:
    def test_health_endpoint(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestReadyProbe:
    """808 审查 M14：ready 端点探活 DeepSeek（mock 客户端，60s 缓存）。"""

    @pytest.fixture(autouse=True)
    def _reset_probe(self):
        from backend.app import main as main_mod

        main_mod._ready_probe["ts"] = 0.0
        main_mod._ready_probe["ok"] = False
        yield
        main_mod._ready_probe["ts"] = 0.0
        main_mod._ready_probe["ok"] = False

    def test_ready_ok_when_api_reachable(self, monkeypatch):
        from unittest.mock import MagicMock

        monkeypatch.setattr("backend.app.main.get_client", lambda: MagicMock())
        resp = client.get("/api/health/ready")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_ready_503_when_api_unreachable(self, monkeypatch):
        from unittest.mock import MagicMock

        bad = MagicMock()
        bad.models.list.side_effect = ConnectionError("api down")
        monkeypatch.setattr("backend.app.main.get_client", lambda: bad)
        resp = client.get("/api/health/ready")
        assert resp.status_code == 503
        assert "unreachable" in resp.json()["reason"]

    def test_probe_result_cached_60s(self, monkeypatch):
        from unittest.mock import MagicMock

        mock_client = MagicMock()
        monkeypatch.setattr("backend.app.main.get_client", lambda: mock_client)
        client.get("/api/health/ready")
        client.get("/api/health/ready")
        assert mock_client.models.list.call_count == 1  # 第二次命中缓存
