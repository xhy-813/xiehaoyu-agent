"""定时清理规则测试（设计文档 §8）。"""

import time

import pytest

from backend.app.services import session_store


@pytest.fixture()
def store(tmp_path):
    session_store.close_store()
    session_store.init_store(tmp_path / "test_sessions.db")
    yield session_store
    session_store.close_store()


def _age_session(store, sid: str, days: int):
    """把会话的 updated_at 改成 N 天前。"""
    old = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - days * 86400))
    with store._lock:
        store._c().execute("UPDATE sessions SET updated_at = ? WHERE id = ?", (old, sid))
        store._c().commit()


class TestCleanup:
    def test_aged_sessions_deleted(self, store):
        fresh = store.create_session("u")
        old = store.create_session("u")
        store.append_message(old, "user", "x")  # 确认 messages 级联
        _age_session(store, old, 40)

        result = store.cleanup(max_age_days=30, max_per_user=50)
        assert result["aged_out"] == 1
        assert store.get_session(old) is None
        assert store.list_messages(old) == []
        assert store.get_session(fresh) is not None

    def test_overflow_per_user_deleted_oldest_first(self, store):
        sids = [store.create_session("u") for _ in range(5)]
        # 造出明确的活跃度顺序：sids[0] 最老
        for i, sid in enumerate(sids):
            _age_session(store, sid, 10 - i)  # 10,9,8,7,6 天前

        result = store.cleanup(max_age_days=30, max_per_user=3)
        assert result["overflow_deleted"] == 2
        remaining = [s["id"] for s in store.list_sessions("u")]
        assert set(remaining) == set(sids[2:])  # 最活跃 3 个保留

    def test_other_users_unaffected(self, store):
        for _ in range(4):
            store.create_session("u1")
        store.create_session("u2")
        result = store.cleanup(max_age_days=30, max_per_user=3)
        assert result["overflow_deleted"] == 1
        assert len(store.list_sessions("u2")) == 1

    def test_nothing_to_clean(self, store):
        store.create_session("u")
        assert store.cleanup(30, 50) == {"aged_out": 0, "overflow_deleted": 0}
