"""X-User-Id 解析与校验（设计文档 §2）。"""

import uuid

import pytest
from fastapi import HTTPException, Request

from backend.app.deps.user import get_user_id, get_user_id_optional


def _make_request(headers: dict[str, str]) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return Request({"type": "http", "method": "GET", "headers": raw})


class TestGetUserId:
    def test_valid_uuid(self):
        uid = str(uuid.uuid4())
        assert get_user_id(_make_request({"x-user-id": uid})) == uid

    def test_missing_raises_400(self):
        with pytest.raises(HTTPException) as exc:
            get_user_id(_make_request({}))
        assert exc.value.status_code == 400

    def test_invalid_raises_400(self):
        with pytest.raises(HTTPException) as exc:
            get_user_id(_make_request({"x-user-id": "not-a-uuid"}))
        assert exc.value.status_code == 400


class TestGetUserIdOptional:
    def test_missing_returns_none(self):
        assert get_user_id_optional(_make_request({})) is None

    def test_valid_returns_value(self):
        uid = str(uuid.uuid4())
        assert get_user_id_optional(_make_request({"x-user-id": uid})) == uid

    def test_invalid_raises_400(self):
        with pytest.raises(HTTPException) as exc:
            get_user_id_optional(_make_request({"x-user-id": "abc"}))
        assert exc.value.status_code == 400
