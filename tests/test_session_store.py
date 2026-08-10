"""session_store CRUD 测试（设计文档 §4）。"""

import pytest

from backend.app.services import session_store


@pytest.fixture()
def store(tmp_path):
    """每个测试用独立的临时 DB 文件。"""
    session_store.close_store()  # 防御：关掉上一个测试遗留的连接
    session_store.init_store(tmp_path / "test_sessions.db")
    yield session_store
    session_store.close_store()


class TestSessions:
    def test_create_and_get(self, store):
        sid = store.create_session("user-a")
        sess = store.get_session(sid)
        assert sess is not None
        assert sess["user_id"] == "user-a"
        assert sess["title"] is None
        assert sess["summary_upto"] == 0

    def test_get_missing_returns_none(self, store):
        assert store.get_session("no-such-id") is None

    def test_list_scoped_by_user_ordered_desc(self, store):
        a1 = store.create_session("user-a")
        a2 = store.create_session("user-a")
        store.create_session("user-b")
        store.append_message(a1, "user", "hi")  # bump a1 的 updated_at
        ids = [s["id"] for s in store.list_sessions("user-a")]
        assert ids[0] == a1 and ids[1] == a2  # a1 刚有消息，排最前

    def test_rename_keeps_updated_at(self, store):
        sid = store.create_session("user-a")
        before = store.get_session(sid)["updated_at"]
        store.rename_session(sid, "我的会话")
        after = store.get_session(sid)
        assert after["title"] == "我的会话"
        assert after["updated_at"] == before

    def test_delete_cascades_messages(self, store):
        sid = store.create_session("user-a")
        store.append_message(sid, "user", "q")
        store.delete_session(sid)
        assert store.get_session(sid) is None
        assert store.list_messages(sid) == []

    def test_search_matches_title_and_content(self, store):
        s1 = store.create_session("user-a")
        store.append_message(s1, "user", "2018 年订单趋势")
        s2 = store.create_session("user-a")
        store.rename_session(s2, "评分分析")
        hits = store.search_sessions("user-a", "订单")
        assert [h["id"] for h in hits] == [s1]
        hits = store.search_sessions("user-a", "评分")
        assert [h["id"] for h in hits] == [s2]
        assert store.search_sessions("user-a", "不存在") == []

    def test_write_after_close_reinitializes(self, tmp_path, monkeypatch):
        """_c() 惰性初始化经 init_store 需重入 _lock——RLock 防自死锁（评审修复）。"""
        session_store.close_store()  # _conn = None
        monkeypatch.setattr(session_store, "_DB_PATH", tmp_path / "lazy.db")
        sid = session_store.create_session("u")  # 写路径持锁时 _c() 触发惰性 init
        assert session_store.get_session(sid)["user_id"] == "u"
        session_store.close_store()


class TestMessages:
    def test_append_and_list(self, store):
        sid = store.create_session("user-a")
        id1 = store.append_message(sid, "user", "问题1")
        id2 = store.append_message(sid, "assistant", "回答1", '[{"tool": "query_data"}]')
        msgs = store.list_messages(sid)
        assert [m["id"] for m in msgs] == [id1, id2]
        assert msgs[1]["artifacts_json"] == '[{"tool": "query_data"}]'

    def test_append_bumps_updated_at(self, store):
        sid = store.create_session("user-a")
        before = store.get_session(sid)["updated_at"]
        store.append_message(sid, "user", "x")
        assert store.get_session(sid)["updated_at"] >= before

    def test_list_messages_after(self, store):
        sid = store.create_session("user-a")
        store.append_message(sid, "user", "q1")
        mid = store.append_message(sid, "assistant", "a1")
        store.append_message(sid, "user", "q2")
        rest = store.list_messages_after(sid, mid)
        assert [m["content"] for m in rest] == ["q2"]

    def test_turn_counts(self, store):
        sid = store.create_session("user-a")
        upto = 0
        for i in range(4):
            store.append_message(sid, "user", f"q{i}")
            upto = store.append_message(sid, "assistant", f"a{i}")
        assert store.count_turns(sid) == 4
        assert store.count_new_turns(sid, upto) == 0
        store.append_message(sid, "user", "q4")
        store.append_message(sid, "assistant", "a4")
        assert store.count_turns(sid) == 5
        assert store.count_new_turns(sid, upto) == 1


class TestMemory:
    def test_memory_context_recent_turns_chronological(self, store):
        sid = store.create_session("user-a")
        for i in range(6):
            store.append_message(sid, "user", f"q{i}")
            store.append_message(sid, "assistant", f"a{i}")
        store.update_summary(sid, "早期摘要", 8)
        ctx = store.get_memory_context(sid, recent_turns=2)
        assert ctx["summary"] == "早期摘要"
        assert ctx["summary_upto"] == 8
        # 最近 2 轮 = q4/a4/q5/a5，按时间正序
        assert [m["content"] for m in ctx["recent"]] == ["q4", "a4", "q5", "a5"]

    def test_memory_context_missing_session(self, store):
        ctx = store.get_memory_context("no-such", 5)
        assert ctx == {"summary": "", "summary_upto": 0, "recent": []}
