"""Unit tests for agent/planner.py — JSON extraction, plan() decision."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.planner import _extract_json, plan


# ── _extract_json tests ─────────────────────────────────────


class TestExtractJson:
    def test_valid_json(self):
        result = _extract_json('{"action": "finalize", "answer": "hello"}')
        assert result == {"action": "finalize", "answer": "hello"}

    def test_json_with_markdown_code_block(self):
        raw = '```json\n{"action": "call", "tool": "query_data"}\n```'
        result = _extract_json(raw)
        assert result["action"] == "call"
        assert result["tool"] == "query_data"

    def test_json_with_plain_code_block(self):
        raw = '```\n{"action": "finalize", "answer": "ok"}\n```'
        result = _extract_json(raw)
        assert result["action"] == "finalize"

    def test_nested_braces(self):
        """Brace counting handles nested braces in answer text."""
        raw = '{"action": "finalize", "answer": "使用 Pandas (Python 库) 分析数据"}'
        result = _extract_json(raw)
        assert result["answer"] == "使用 Pandas (Python 库) 分析数据"

    def test_nested_json_in_answer(self):
        """Brace counting handles nested JSON-like structures."""
        raw = '{"action": "finalize", "answer": "结果：{\\"count\\": 123}"}'
        result = _extract_json(raw)
        assert result["action"] == "finalize"
        assert "123" in result["answer"]

    def test_multiple_json_objects_extracts_first(self):
        raw = '{"action": "finalize", "answer": "first"}\nextra text\n{"action": "call"}'
        result = _extract_json(raw)
        # Should parse the first complete JSON object
        assert "action" in result

    def test_no_json_raises(self):
        with pytest.raises(ValueError, match="not valid JSON"):
            _extract_json("just some text without braces")

    def test_unmatched_braces_raises(self):
        with pytest.raises((ValueError, json.JSONDecodeError)):
            _extract_json('{"action": "call", "tool": "test"')

    def test_extra_text_around_json(self):
        raw = 'Some prefix text\n{"action": "finalize", "answer": "ok"}\nSome suffix'
        result = _extract_json(raw)
        assert result["action"] == "finalize"

    def test_deeply_nested_braces(self):
        """Multiple levels of nesting in the answer string."""
        raw = (
            '{"action": "finalize", '
            '"answer": "订单数据：\\n{'
            '\\"total\\": 100, '
            '\\"items\\": [{\\"name\\": \\"A\\", \\"qty\\": 50}]'
            '}"}'
        )
        result = _extract_json(raw)
        assert result["action"] == "finalize"

    # ── 808 审查 H1 回归用例：多行 JSON 必须可解析 ──

    def test_pretty_multiline_json(self):
        """LLM 美化输出（结构性换行/缩进）必须正常解析（808 审查 H1 回归）。

        _sanitize_control_chars 只允许转义字符串值内部的控制字符；
        token 之间的换行是合法 JSON 空白，不得破坏。
        """
        raw = '{\n  "action": "finalize",\n  "answer": "你好"\n}'
        result = _extract_json(raw)
        assert result == {"action": "finalize", "answer": "你好"}

    def test_fenced_multiline_json(self):
        """markdown 围栏包裹的多行 JSON 必须正常解析（808 审查 H1 回归）。"""
        raw = (
            '```json\n'
            '{\n'
            '  "action": "call",\n'
            '  "tool": "query_data",\n'
            '  "args": {"question": "订单数"}\n'
            '}\n'
            '```'
        )
        result = _extract_json(raw)
        assert result["action"] == "call"
        assert result["tool"] == "query_data"

    def test_literal_newline_inside_string_still_escaped(self):
        """修复目标场景不得回退：字符串值内的裸换行仍被转义后可解析。"""
        raw = '{"action": "finalize", "answer": "第一行\n第二行"}'
        result = _extract_json(raw)
        assert result["answer"] == "第一行\n第二行"

    def test_brace_inside_string_not_counted(self):
        """兜底大括号计数必须跳过字符串值内部的括号。"""
        raw = '{"action": "finalize", "answer": "用 } 收尾"}\ntrailing {"action": "call"}'
        result = _extract_json(raw)
        assert result["answer"] == "用 } 收尾"


# ── plan() tests ────────────────────────────────────────────


class TestPlan:
    @pytest.fixture
    def mock_client(self):
        m = MagicMock()
        m.chat.completions.create = AsyncMock()
        return m

    def test_call_action(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content='{"action": "call", "tool": "query_data", "args": {"question": "test"}}'
                    )
                )
            ]
        )
        result = asyncio.run(plan("hello", [], client=mock_client))
        assert result["action"] == "call"
        assert result["tool"] == "query_data"

    def test_finalize_action(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content='{"action": "finalize", "answer": "你好！我是谢浩宇的数字分身。"}'
                    )
                )
            ]
        )
        result = asyncio.run(plan("你好", [], client=mock_client))
        assert result["action"] == "finalize"
        assert "谢浩宇" in result["answer"]

    def test_with_trace_context(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content='{"action": "finalize", "answer": "根据查询结果，2018年共有12个月的数据。"}'
                    )
                )
            ]
        )
        trace = [
            {
                "tool": "query_data",
                "args": {"question": "2018 年每月订单数"},
                "summary": "SQL: SELECT ...\n行数: 12\n前10行:\n...",
            }
        ]
        result = asyncio.run(plan("2018 年每月订单数", trace, client=mock_client))
        assert result["action"] == "finalize"

    def test_empty_trace(self, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content='{"action": "call", "tool": "introduce_me", "args": {"question": "你是谁"}}'
                    )
                )
            ]
        )
        result = asyncio.run(plan("你是谁", [], client=mock_client))
        assert result["action"] == "call"
        assert result["tool"] == "introduce_me"

    def test_uses_default_client(self):
        with patch("agent.planner.get_async_client") as mock_get_async_client:
            c = MagicMock()
            c.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[
                        MagicMock(
                            message=MagicMock(
                                content='{"action": "finalize", "answer": "ok"}'
                            )
                        )
                    ]
                )
            )
            c.close = AsyncMock()  # 未注入 client 时 finally 会 await close()
            mock_get_async_client.return_value = c
            result = asyncio.run(plan("test", []))
            assert result["action"] == "finalize"
            mock_get_async_client.assert_called_once()