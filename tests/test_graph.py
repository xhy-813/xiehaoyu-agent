"""Unit tests for agent/graph.py — state machine, router, tool dispatch."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agent.graph import (
    TOOLS,
    _TOOL_NAMES,
    _run_tool,
    _summarize,
    build_graph,
    finalize_node,
    planner_node,
    router,
)
from agent.planner import plan


# ── Tool registry tests ─────────────────────────────────────


class TestToolRegistry:
    def test_all_tools_registered(self):
        """Every tool in the agent must be in the TOOLS registry."""
        assert set(TOOLS.keys()) == {
            "introduce_me",
            "query_data",
            "visualize",
            "explain_result",
        }

    def test__tool_names_synced_with_tools(self):
        assert set(_TOOL_NAMES) == set(TOOLS.keys())

    def test_adding_tool_to_registry_picks_up_in_graph(self):
        """The build_graph uses _TOOL_NAMES to add nodes."""
        g = build_graph()
        # The graph should have been compiled successfully
        assert g is not None


# ── Router tests ────────────────────────────────────────────


class TestRouter:
    def test_returns_tool_name(self):
        state = {"step": 1, "next_action": "call", "next_tool": "query_data"}
        assert router(state) == "query_data"

    def test_returns_finalize_when_max_steps(self):
        state = {"step": 5, "next_action": "call", "next_tool": "query_data"}
        assert router(state) == "finalize"

    def test_returns_finalize_when_planner_says_finalize(self):
        state = {"step": 1, "next_action": "finalize"}
        assert router(state) == "finalize"

    def test_returns_finalize_for_unknown_tool(self):
        state = {"step": 1, "next_action": "call", "next_tool": "unknown_tool"}
        assert router(state) == "finalize"

    def test_step_zero_not_exceeded(self):
        state = {"step": 0, "next_action": "call", "next_tool": "introduce_me"}
        assert router(state) == "introduce_me"


# ── finalize_node tests ─────────────────────────────────────


class TestFinalizeNode:
    def test_returns_existing_answer(self):
        state = {"final_answer": "Hello world"}
        result = finalize_node(state)
        assert result["final_answer"] == "Hello world"

    def test_fallback_from_trace(self):
        state = {"final_answer": "", "trace": [{"summary": "last result"}]}
        result = finalize_node(state)
        assert "last result" in result["final_answer"]

    def test_fallback_empty(self):
        state = {"final_answer": "", "trace": []}
        result = finalize_node(state)
        assert result["final_answer"] == "未能生成回答。"


# ── _summarize tests ────────────────────────────────────────


class TestSummarize:
    def test_introduce_me_summary(self):
        r = type("R", (), {"answer": "我是谢浩宇，来自吉首大学。"})()
        result = _summarize("introduce_me", r)
        assert "谢浩宇" in result

    def test_visualize_summary(self):
        r = type("R", (), {"chart_type": "line", "reason": "time series"})()
        result = _summarize("visualize", r)
        assert "line" in result
        assert "time series" in result

    def test_explain_result_summary(self):
        result = _summarize("explain_result", "2018 年月订单量呈上升趋势")
        assert "上升趋势" in result

    def test_unknown_tool_fallback(self):
        result = _summarize("unknown", "some text")
        assert result == "some text"


# ── _run_tool tests ─────────────────────────────────────────


class TestRunTool:
    def test_unknown_tool_returns_error_trace(self):
        """Unknown tool is caught and recorded as an error trace entry."""
        state = {"question": "test", "trace": []}
        result = _run_tool("nonexistent", {}, state)
        assert "失败" in result["trace"][-1]["summary"]
        assert "nonexistent" in result["trace"][-1]["tool"]

    def test_visualize_without_df(self):
        state = {"question": "test", "trace": [], "last_df": None}
        result = _run_tool("visualize", {"question": "test"}, state)
        assert "错误" in result["trace"][-1]["summary"]

    def test_explain_result_without_df(self):
        state = {"question": "test", "trace": [], "last_df": None, "last_sql": ""}
        result = _run_tool("explain_result", {"question": "test"}, state)
        assert "错误" in result["trace"][-1]["summary"]


# ── planner_node tests ──────────────────────────────────────


class TestPlannerNode:
    def test_finalize_action(self):
        with patch("agent.graph.plan") as mock_plan:
            mock_plan.return_value = {"action": "finalize", "answer": "done"}
            state = {"question": "hi", "trace": [], "step": 0}
            result = planner_node(state)
            assert result["next_action"] == "finalize"
            assert result["final_answer"] == "done"

    def test_call_action(self):
        with patch("agent.graph.plan") as mock_plan:
            mock_plan.return_value = {
                "action": "call",
                "tool": "query_data",
                "args": {"question": "how many orders?"},
            }
            state = {"question": "how many orders?", "trace": [], "step": 0}
            result = planner_node(state)
            assert result["next_action"] == "call"
            assert result["next_tool"] == "query_data"

    def test_planner_error_fallback(self):
        with patch("agent.graph.plan", side_effect=RuntimeError("API failed")):
            state = {"question": "test", "trace": [], "step": 0}
            result = planner_node(state)
            assert result["next_action"] == "finalize"
            assert "失败" in result["final_answer"]


# ── build_graph tests ───────────────────────────────────────


class TestBuildGraph:
    def test_graph_compiles(self):
        g = build_graph()
        assert g is not None
        # The compiled graph should have the expected structure
        assert hasattr(g, "invoke")
        assert hasattr(g, "astream")