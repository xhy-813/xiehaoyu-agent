"""LangGraph state machine.

planner → tool_router → tools → planner (loop, max 5) → finalize

用法：
    from agent.graph import run
    result = run("2018 年每月订单数，帮我画个图")
    print(result["answer"])
    for t in result["trace"]:
        print(t)
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator, TypedDict

import pandas as pd
import plotly.graph_objects as go
from langgraph.graph import END, START, StateGraph

from agent.planner import plan
from agent.tools.explain_result import explain_result
from agent.tools.introduce_me import introduce_me
from agent.tools.query_data import query_data
from agent.tools.visualize import visualize
from configs.settings import settings


class AgentState(TypedDict, total=False):
    question: str
    trace: list[dict]
    last_df: Any  # pd.DataFrame
    last_sql: str
    final_answer: str
    step: int
    next_action: str  # "call" | "finalize"
    next_tool: str
    next_args: dict


MAX_STEPS = settings.max_agent_steps


# ── Helpers ──────────────────────────────────────────────


def _summarize(tool: str, result: Any) -> str:
    """Short text summary of a tool result for planner context."""
    if tool == "introduce_me":
        return result.answer[:800]
    if tool == "query_data":
        head = result.df.head(10).to_string(index=False)
        return f"SQL: {result.sql}\n行数: {len(result.df)}\n前10行:\n{head}"
    if tool == "visualize":
        return f"图表类型: {result.chart_type}（{result.reason}）"
    if tool == "explain_result":
        return str(result)[:800]
    return str(result)[:800]


def _run_tool(tool: str, args: dict, state: AgentState) -> dict:
    """Execute one tool, return state patch."""
    question = args.get("question", state["question"])
    trace = state.get("trace", [])

    if tool == "introduce_me":
        r = introduce_me(question)
        artifact = {"answer": r.answer, "citations": r.citations}
        return {"trace": trace + [{"tool": tool, "args": args, "summary": _summarize(tool, r), "artifact": artifact}]}

    if tool == "query_data":
        r = query_data(question)
        artifact = {"sql": r.sql, "df": r.df}
        return {
            "trace": trace + [{"tool": tool, "args": args, "summary": _summarize(tool, r), "artifact": artifact}],
            "last_df": r.df,
            "last_sql": r.sql,
        }

    if tool == "visualize":
        df = state.get("last_df")
        if df is None:
            return {"trace": trace + [{"tool": tool, "args": args, "summary": "错误: 没有数据，请先调用 query_data", "artifact": None}]}
        r = visualize(df, question)
        artifact = {"figure": r.figure, "chart_type": r.chart_type}
        return {"trace": trace + [{"tool": tool, "args": args, "summary": _summarize(tool, r), "artifact": artifact}]}

    if tool == "explain_result":
        df = state.get("last_df")
        sql = state.get("last_sql", "")
        if df is None:
            return {"trace": trace + [{"tool": tool, "args": args, "summary": "错误: 没有数据，请先调用 query_data", "artifact": None}]}
        r = explain_result(question, sql, df)
        artifact = {"insight": r}
        return {"trace": trace + [{"tool": tool, "args": args, "summary": _summarize(tool, r), "artifact": artifact}]}

    raise ValueError(f"Unknown tool: {tool}")


# ── Nodes ────────────────────────────────────────────────


def planner_node(state: AgentState) -> dict:
    """Ask LLM what to do next."""
    step = state.get("step", 0)
    decision = plan(state["question"], state.get("trace", []))

    if decision.get("action") == "finalize":
        return {
            "final_answer": decision.get("answer", ""),
            "next_action": "finalize",
            "step": step + 1,
        }

    return {
        "next_action": "call",
        "next_tool": decision.get("tool", ""),
        "next_args": decision.get("args", {}),
        "step": step + 1,
    }


def _make_tool_node(tool_name: str):
    """Factory: create a node that executes *tool_name*."""

    def node(state: AgentState) -> dict:
        return _run_tool(tool_name, state.get("next_args", {}), state)

    return node


def finalize_node(state: AgentState) -> dict:
    """Emit final answer (fallback if max-steps reached without explicit finalize)."""
    answer = state.get("final_answer", "")
    if not answer:
        trace = state.get("trace", [])
        if trace:
            answer = "已达到最大步数，最后结果：\n" + trace[-1].get("summary", "")
        else:
            answer = "未能生成回答。"
    return {"final_answer": answer}


# ── Router ───────────────────────────────────────────────


def router(state: AgentState) -> str:
    """Conditional edge: planner → tool | finalize."""
    step = state.get("step", 0)

    if step > MAX_STEPS:
        return "finalize"

    if state.get("next_action") == "finalize":
        return "finalize"

    tool = state.get("next_tool", "")
    if tool in ("introduce_me", "query_data", "visualize", "explain_result"):
        return tool

    return "finalize"


# ── Build ────────────────────────────────────────────────


def build_graph():
    """Compile the LangGraph state machine."""
    g = StateGraph(AgentState)

    g.add_node("planner", planner_node)
    g.add_node("introduce_me", _make_tool_node("introduce_me"))
    g.add_node("query_data", _make_tool_node("query_data"))
    g.add_node("visualize", _make_tool_node("visualize"))
    g.add_node("explain_result", _make_tool_node("explain_result"))
    g.add_node("finalize", finalize_node)

    g.add_edge(START, "planner")

    g.add_conditional_edges(
        "planner",
        router,
        {
            "introduce_me": "introduce_me",
            "query_data": "query_data",
            "visualize": "visualize",
            "explain_result": "explain_result",
            "finalize": "finalize",
        },
    )

    # Tools loop back to planner
    g.add_edge("introduce_me", "planner")
    g.add_edge("query_data", "planner")
    g.add_edge("visualize", "planner")
    g.add_edge("explain_result", "planner")
    g.add_edge("finalize", END)

    return g.compile()


# ── Serialization helpers ────────────────────────────────


def _serialize_artifact(artifact: dict | None) -> dict | None:
    """Convert non-serializable objects (DataFrame, Plotly Figure) to JSON-safe dict."""
    if artifact is None:
        return None

    result = dict(artifact)

    # DataFrame → JSON
    if "df" in result:
        df = result.pop("df")
        if isinstance(df, pd.DataFrame):
            result["df_json"] = df.head(500).to_json(orient="records", date_format="iso", force_ascii=False)
            result["df_shape"] = {"rows": len(df), "cols": len(df.columns)}
            result["df_columns"] = list(df.columns)

    # Plotly Figure → JSON
    if "figure" in result:
        fig = result.pop("figure")
        if isinstance(fig, go.Figure):
            result["figure_json"] = fig.to_json()

    return result


# ── Streaming entry point ────────────────────────────────


async def stream_run(question: str) -> AsyncIterator[dict]:
    """Async streaming agent runner.

    Uses LangGraph's built-in ``astream()`` to yield one event per node
    execution.  Each event looks like::

        {"type": "planner_decision" | "tool_end" | "final_answer",
         "node": str,
         "data": {...}}

    The ``data`` dict for ``tool_end`` events contains the full trace entry
    (including a serialized artifact), ready for SSE delivery.
    """
    app = build_graph()
    initial_state: AgentState = {
        "question": question,
        "trace": [],
        "step": 0,
    }

    async for event in app.astream(initial_state, stream_mode="updates"):
        for node_name, state_update in event.items():
            if node_name == "finalize":
                yield {
                    "type": "final_answer",
                    "node": node_name,
                    "data": {
                        "answer": state_update.get("final_answer", ""),
                        "steps": state_update.get("step", 0),
                    },
                }
            elif node_name == "planner":
                # Expose planner decisions so the frontend can show "thinking…"
                yield {
                    "type": "planner_decision",
                    "node": node_name,
                    "data": {
                        "next_action": state_update.get("next_action", ""),
                        "next_tool": state_update.get("next_tool", ""),
                        "step": state_update.get("step", 0),
                    },
                }
            else:
                # Tool node: introduce_me / query_data / visualize / explain_result
                new_trace = state_update.get("trace", [])
                if new_trace:
                    latest = new_trace[-1]
                    yield {
                        "type": "tool_end",
                        "node": node_name,
                        "data": {
                            "tool": latest.get("tool", node_name),
                            "args": latest.get("args", {}),
                            "summary": latest.get("summary", ""),
                            "artifact": _serialize_artifact(latest.get("artifact")),
                        },
                    }


# ── Synchronous entry point (kept for backward compat) ──


def run(question: str) -> dict:
    """Run the agent end-to-end.

    Returns:
        {"answer": str, "trace": list[dict], "steps": int}
    """
    app = build_graph()
    result = app.invoke({
        "question": question,
        "trace": [],
        "step": 0,
    })
    return {
        "answer": result.get("final_answer", ""),
        "trace": result.get("trace", []),
        "steps": result.get("step", 0),
    }
