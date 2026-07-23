"""Streamlit chat component."""

from __future__ import annotations

import streamlit as st

from agent.graph import run
from ui.auth import check_rate_limit


EXAMPLE_QUESTIONS = [
    "📝 介绍一下你自己",
    "📊 2018年每月订单数，帮我画个图",
    "🔍 销量 top 5 的商品品类有哪些？",
    "💰 各州客户数 top 10",
]


def _init_state() -> None:
    """Initialize session state for chat."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "last_result" not in st.session_state:
        st.session_state["last_result"] = None


def _render_welcome() -> None:
    """渲染欢迎消息和示例问题（当无对话历史时）。"""
    if st.session_state["messages"]:
        return

    with st.chat_message("assistant"):
        st.markdown(
            "你好！我是**谢浩宇 Agent**，可以帮你：\n\n"
            "🔹 **了解谢浩宇** — 项目经历、技术栈、实习经验\n"
            "🔹 **查询电商数据** — Olist 巴西电商数据集的 Text2SQL 查询\n"
            "🔹 **数据可视化** — 自动选图 + 业务洞察解读\n\n"
            "试试以下问题，或直接输入你想问的："
        )

    # 示例问题按钮
    cols = st.columns(len(EXAMPLE_QUESTIONS))
    for col, q in zip(cols, EXAMPLE_QUESTIONS):
        if col.button(q, use_container_width=True, key=f"example_{q}"):
            # 模拟用户输入
            st.session_state["_pending_input"] = q.replace("📝 ", "").replace("📊 ", "").replace("🔍 ", "").replace("💰 ", "")
            st.rerun()


def render_chat() -> None:
    """Render chat history + input. Call agent on user input."""
    _init_state()

    # 检查是否有示例问题待处理
    pending = st.session_state.pop("_pending_input", None)

    # 渲染欢迎消息或历史消息
    if not st.session_state["messages"]:
        _render_welcome()
    else:
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if msg.get("steps"):
                    st.caption(f"⚡ 执行步数: {msg['steps']}")

    # 获取输入（chat_input 或待处理的示例问题）
    prompt = pending or st.chat_input("请输入问题…")

    if not prompt:
        return

    # 限流检查
    if not check_rate_limit():
        return

    # 渲染用户消息
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 调用 agent
    with st.chat_message("assistant"):
        with st.spinner("🤔 思考中…"):
            try:
                result = run(prompt)
            except Exception as e:
                st.error(f"❌ 执行出错: {e}")
                st.session_state["messages"].append(
                    {"role": "assistant", "content": f"❌ 执行出错: {e}"}
                )
                return

        answer = result.get("answer", "")
        steps = result.get("steps", 0)
        trace = result.get("trace", [])

        st.markdown(answer)

        # 显示工具调用摘要
        if trace:
            tools_used = " → ".join(t["tool"] for t in trace)
            st.caption(f"⚡ {steps} 步 ｜ 🔧 {tools_used}")

        # 存储结果
        st.session_state["messages"].append(
            {"role": "assistant", "content": answer, "steps": steps}
        )
        st.session_state["last_result"] = result

    # 触发右侧面板刷新
    st.rerun()
