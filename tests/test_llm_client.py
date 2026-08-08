"""Unit tests for agent/llm_client.py — token usage logging wrapper (808 审查 M10)。"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from agent.llm_client import logged_chat_create


@pytest.fixture()
def llm_log_records():
    """直接挂 handler 到 agent.llm_client logger（caplog 依赖 root 传播，
    而 backend main 的 dictConfig 将 agent logger 设为 propagate=False，
    全量运行时 caplog 会收不到）。"""
    records: list[str] = []

    class _H(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record.getMessage())

    lg = logging.getLogger("agent.llm_client")
    h = _H()
    lg.addHandler(h)
    lg.setLevel(logging.INFO)
    yield records
    lg.removeHandler(h)


class TestLoggedChatCreate:
    def test_logs_token_usage(self, llm_log_records):
        client = MagicMock()
        client.chat.completions.create.return_value = MagicMock(
            usage=MagicMock(prompt_tokens=120, completion_tokens=30, total_tokens=150)
        )
        resp = logged_chat_create(
            client, model="deepseek-v4-flash", messages=[], temperature=0.0, caller="test"
        )
        assert resp is client.chat.completions.create.return_value
        text = "\n".join(llm_log_records)
        assert "caller=test" in text
        assert "prompt=120" in text
        assert "total=150" in text

    def test_missing_usage_does_not_crash(self, llm_log_records):
        """响应无 usage 字段时静默跳过（不报错）。"""
        client = MagicMock()
        client.chat.completions.create.return_value = MagicMock(spec=[])  # 无 usage 属性
        logged_chat_create(client, model="m", messages=[], caller="test")
        assert not any("llm_tokens" in m for m in llm_log_records)

    def test_call_args_passed_through(self):
        client = MagicMock()
        logged_chat_create(client, model="m", messages=[{"role": "user", "content": "hi"}],
                           temperature=0.3, caller="planner")
        kwargs = client.chat.completions.create.call_args.kwargs
        assert kwargs["model"] == "m"
        assert kwargs["temperature"] == 0.3
        assert "caller" not in kwargs  # caller 不得透传给 API
