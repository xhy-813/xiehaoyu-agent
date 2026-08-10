"""chat 持久化 + 记忆注入 + 匿名兼容测试（设计文档 §5/§10）。"""

import os
os.environ["SKIP_CONFIG_VALIDATION"] = "1"  # 与 test_public_chat.py 相同：导入 app 前设置

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.deps.rate_limit import _hourly_buckets, _daily_state
from backend.app.services import session_store

client = TestClient(app)

USER_A = {"X-User-Id": str(uuid.uuid4())}
USER_B = {"X-User-Id": str(uuid.uuid4())}


@pytest.fixture(autouse=True)
def _clean_rate_limit():
    _hourly_buckets.clear()
    _daily_state["date"] = ""
    _daily_state["count"] = 0
    yield
    _hourly_buckets.clear()


@pytest.fixture()
def store(tmp_path):
    session_store.close_store()
    session_store.init_store(tmp_path / "test_sessions.db")
    yield session_store
    session_store.close_store()


@pytest.fixture()
def fake_agent(monkeypatch):
    """替换 stream_run 与 summarizer 后台任务，避免真实 LLM 调用。"""

    def _fake_stream(question: str, history_text: str = ""):
        async def gen():
            yield {
                "type": "tool_end",
                "node": "query_data",
                "data": {
                    "tool": "query_data",
                    "args": {"question": question},
                    "summary": "SQL: SELECT 1\n行数: 1",
                    "artifact": {"sql": "SELECT 1", "df_json": '[{"a": 1}]'},
                    "status": "ok",
                },
            }
            yield {"type": "final_answer", "node": "finalize", "data": {"answer": "分析完成", "steps": 2}}

        return gen()

    async def _noop(*args, **kwargs):
        return False

    monkeypatch.setattr("backend.app.routers.chat.stream_run", _fake_stream)
    monkeypatch.setattr("backend.app.services.summarizer.maybe_summarize", _noop)
    monkeypatch.setattr("backend.app.services.summarizer.generate_title", _noop)
    return _fake_stream


class TestAnonymousCompat:
    def test_anonymous_chat_works_and_persists_nothing(self, store, fake_agent):
        """无 X-User-Id：行为与现状一致，不落库。"""
        resp = client.post("/api/chat", json={"question": "你好"})
        assert resp.status_code == 200
        assert "final_answer" in resp.text
        assert "x-session-id" not in {k.lower() for k in resp.headers.keys()}


class TestPersistence:
    def test_implicit_session_creation_returns_header(self, store, fake_agent):
        resp = client.post("/api/chat", json={"question": "查订单"}, headers=USER_A)
        assert resp.status_code == 200
        sid = resp.headers.get("x-session-id")
        assert sid
        msgs = store.list_messages(sid)
        assert [m["role"] for m in msgs] == ["user", "assistant"]
        assert msgs[0]["content"] == "查订单"
        assert msgs[1]["content"] == "分析完成"
        trace = json.loads(msgs[1]["artifacts_json"])
        assert trace[0]["tool"] == "query_data"
        assert isinstance(trace[0]["artifact"]["df_json"], str)

    def test_explicit_session_used(self, store, fake_agent):
        sid = store.create_session(USER_A["X-User-Id"])
        resp = client.post(
            "/api/chat", json={"question": "q", "session_id": sid}, headers=USER_A
        )
        assert resp.status_code == 200
        assert "x-session-id" not in {k.lower() for k in resp.headers.keys()}
        assert len(store.list_messages(sid)) == 2

    def test_foreign_session_403(self, store, fake_agent):
        sid = store.create_session(USER_A["X-User-Id"])
        resp = client.post(
            "/api/chat", json={"question": "q", "session_id": sid}, headers=USER_B
        )
        assert resp.status_code == 403

    def test_unknown_session_404(self, store, fake_agent):
        resp = client.post(
            "/api/chat",
            json={"question": "q", "session_id": str(uuid.uuid4())},
            headers=USER_A,
        )
        assert resp.status_code == 404

    def test_invalid_user_id_400(self, store, fake_agent):
        resp = client.post("/api/chat", json={"question": "q"}, headers={"X-User-Id": "abc"})
        assert resp.status_code == 400


class TestMemoryInjection:
    def test_history_text_reaches_stream_run(self, store, fake_agent, monkeypatch):
        """多轮后第二次提问，stream_run 收到含最近对话的 history_text。"""
        captured = {}

        def _capturing_stream(question: str, history_text: str = ""):
            captured["history_text"] = history_text

            async def gen():
                yield {"type": "final_answer", "node": "finalize", "data": {"answer": "ok", "steps": 1}}

            return gen()

        monkeypatch.setattr("backend.app.routers.chat.stream_run", _capturing_stream)
        sid = store.create_session(USER_A["X-User-Id"])
        store.append_message(sid, "user", "2018 年订单趋势如何")
        store.append_message(sid, "assistant", "2018 年整体上涨")

        resp = client.post(
            "/api/chat", json={"question": "那 2017 年呢", "session_id": sid}, headers=USER_A
        )
        assert resp.status_code == 200
        assert "[最近对话]" in captured["history_text"]
        assert "2018 年订单趋势如何" in captured["history_text"]
