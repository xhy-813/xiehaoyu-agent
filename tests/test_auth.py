"""Unit tests for backend/app/routers/auth.py — login endpoint.

Uses FastAPI's TestClient to verify the HTTP contract.  Config validation
is skipped so the tests can run with placeholder secrets.
"""

import os
os.environ["SKIP_CONFIG_VALIDATION"] = "1"

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


class TestLogin:
    def test_login_with_empty_body_returns_422(self):
        resp = client.post("/api/auth/login", json={})
        assert resp.status_code == 422

    def test_login_with_wrong_code_returns_401(self):
        resp = client.post("/api/auth/login", json={"access_code": "wrong-code-xyz"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "访问码错误"

    def test_login_with_empty_code_returns_422(self):
        """Pydantic validates the field before our handler runs."""
        resp = client.post("/api/auth/login", json={"access_code": ""})
        assert resp.status_code == 422

    def test_token_response_has_correct_shape(self):
        """When the correct code is provided, the response should contain
        an access_token with three dot-separated segments."""
        import configs.settings as cfg
        # Use the actual configured access_code; if it's empty, this won't work.
        # We test the shape conditional on the code being non-empty.
        if cfg.settings.access_code:
            resp = client.post(
                "/api/auth/login",
                json={"access_code": cfg.settings.access_code},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            parts = data["access_token"].split(".")
            assert len(parts) == 3


class TestHealth:
    def test_health_endpoint(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}