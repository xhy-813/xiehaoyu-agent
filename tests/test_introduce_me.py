"""Unit tests for agent/tools/introduce_me.py — RAG tool with mocked
retriever and LLM client (808 审查 M9/L16：此前仅 smoke 脚本覆盖）。"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from agent.tools.introduce_me import introduce_me
from rag.retriever import Hit, RetrievalResult


def _hit(content: str = "谢浩宇，吉首大学数据科学专业") -> Hit:
    return Hit(content=content, source="简历/谢浩宇-简历.md", heading="基本信息", distance=0.2)


def _mock_client(answer: str = "我是谢浩宇……") -> MagicMock:
    client = MagicMock()
    client.chat.completions.create = AsyncMock(
        return_value=MagicMock(choices=[MagicMock(message=MagicMock(content=answer))])
    )
    client.close = AsyncMock()  # 未注入 client 时 finally 会 await close()
    return client


class TestIntroduceMe:
    def test_normal_path_returns_answer_and_citations(self):
        client = _mock_client()
        with (
            patch(
                "agent.tools.introduce_me.retrieve_result",
                return_value=RetrievalResult([_hit()], degraded=False),
            ),
            patch("agent.tools.introduce_me.get_async_client", return_value=client),
        ):
            result = introduce_me("介绍一下你自己")

        assert result.answer == "我是谢浩宇……"
        assert result.degraded is False
        assert result.citations[0]["source"] == "简历/谢浩宇-简历.md"
        # LLM 收到的 prompt 应包含检索片段
        messages = client.chat.completions.create.call_args.kwargs["messages"]
        assert "谢浩宇，吉首大学" in messages[1]["content"]

    def test_degraded_path_instructs_honesty(self):
        """808 审查 M9：检索基础设施故障 → prompt 必须包含"不要编造"指令。"""
        client = _mock_client("知识库暂时不可用")
        with (
            patch(
                "agent.tools.introduce_me.retrieve_result",
                return_value=RetrievalResult([], degraded=True),
            ),
            patch("agent.tools.introduce_me.get_async_client", return_value=client),
        ):
            result = introduce_me("介绍一下你自己")

        assert result.degraded is True
        messages = client.chat.completions.create.call_args.kwargs["messages"]
        assert "不要凭印象编造" in messages[1]["content"]
        assert "知识库检索当前不可用" in messages[1]["content"]

    def test_llm_failure_raises_runtime_error(self):
        client = _mock_client()
        client.chat.completions.create.side_effect = RuntimeError("api down")  # AsyncMock 保留
        with (
            patch(
                "agent.tools.introduce_me.retrieve_result",
                return_value=RetrievalResult([_hit()], degraded=False),
            ),
            patch("agent.tools.introduce_me.get_async_client", return_value=client),
        ):
            import pytest

            with pytest.raises(RuntimeError, match="introduce_me LLM call failed"):
                introduce_me("你是谁")
