"""会话 CRUD + 回放协议测试（设计文档 §5）。"""

import os
os.environ["SKIP_CONFIG_VALIDATION"] = "1"  # 与 test_public_chat.py 相同：导入 app 前设置，防收集期 _validate() sys.exit

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import session_store

client = TestClient(app)

USER_A = {"X-User-Id": str(uuid.uuid4())}
USER_B = {"X-User-Id": str(uuid.uuid4())}


@pytest.fixture()
def store(tmp_path):
    session_store.close_store()
    session_store.init_store(tmp_path / "test_sessions.db")
    yield session_store
    session_store.close_store()


def _create(headers) -> str:
    resp = client.post("/api/sessions", headers=headers)
    assert resp.status_code == 200
    return resp.json()["session_id"]


class TestIdentity:
    def test_missing_user_id_400(self, store):
        assert client.post("/api/sessions").status_code == 400

    def test_invalid_user_id_400(self, store):
        assert client.post("/api/sessions", headers={"X-User-Id": "abc"}).status_code == 400


class TestCRUD:
    def test_create_and_list(self, store):
        sid = _create(USER_A)
        resp = client.get("/api/sessions", headers=USER_A)
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()["sessions"]]
        assert sid in ids

    def test_list_isolated_per_user(self, store):
        _create(USER_A)
        resp = client.get("/api/sessions", headers=USER_B)
        assert resp.json()["sessions"] == []

    def test_rename(self, store):
        sid = _create(USER_A)
        resp = client.patch(f"/api/sessions/{sid}", json={"title": "新标题"}, headers=USER_A)
        assert resp.status_code == 200
        sess = store.get_session(sid)
        assert sess["title"] == "新标题"

    def test_rename_empty_title_422(self, store):
        sid = _create(USER_A)
        resp = client.patch(f"/api/sessions/{sid}", json={"title": ""}, headers=USER_A)
        assert resp.status_code == 422

    def test_delete(self, store):
        sid = _create(USER_A)
        assert client.delete(f"/api/sessions/{sid}", headers=USER_A).status_code == 200
        assert store.get_session(sid) is None

    def test_search(self, store):
        sid = _create(USER_A)
        store.append_message(sid, "user", "2018 年订单趋势")
        resp = client.get("/api/sessions/search", params={"q": "订单"}, headers=USER_A)
        assert resp.status_code == 200  # 若路由顺序错了会被 /{session_id} 吞掉变 404/400
        assert [s["id"] for s in resp.json()["sessions"]] == [sid]


class TestOwnership:
    def test_get_403_for_other_user(self, store):
        sid = _create(USER_A)
        assert client.get(f"/api/sessions/{sid}", headers=USER_B).status_code == 403

    def test_patch_403_for_other_user(self, store):
        sid = _create(USER_A)
        resp = client.patch(f"/api/sessions/{sid}", json={"title": "x"}, headers=USER_B)
        assert resp.status_code == 403

    def test_delete_403_for_other_user(self, store):
        sid = _create(USER_A)
        assert client.delete(f"/api/sessions/{sid}", headers=USER_B).status_code == 403

    def test_get_404_for_unknown(self, store):
        assert client.get(f"/api/sessions/{uuid.uuid4()}", headers=USER_A).status_code == 404


class TestReplay:
    def test_replay_shape(self, store):
        sid = _create(USER_A)
        trace = [
            {"tool": "query_data", "args": {"question": "q"}, "summary": "s",
             "artifact": {"sql": "SELECT 1", "df_json": '[{"a": 1}]',
                          "df_shape": {"rows": 1, "cols": 1}, "df_columns": ["a"]}},
            {"tool": "visualize", "args": {"question": "q"}, "summary": "s2",
             "artifact": {"figure_json": '{"data": []}', "chart_type": "bar"}},
        ]
        store.append_message(sid, "user", "问题")
        store.append_message(sid, "assistant", "回答", json.dumps(trace, ensure_ascii=False))

        resp = client.get(f"/api/sessions/{sid}", headers=USER_A)
        assert resp.status_code == 200
        body = resp.json()
        assert body["session"]["id"] == sid
        user_msg, asst = body["messages"]
        assert user_msg["role"] == "user" and user_msg["trace"] is None
        assert asst["steps"] == 2
        assert asst["tools"] == ["query_data", "visualize"]  # 有序去重
        # df_json/figure_json 必须原样返回 JSON 字符串（前端组件自行 parse）
        assert isinstance(asst["trace"][0]["artifact"]["df_json"], str)
        assert isinstance(asst["trace"][1]["artifact"]["figure_json"], str)
