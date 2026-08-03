"""Streamlit chat component."""

from __future__ import annotations

import streamlit as st

from agent.graph import run


EXAMPLE_GROUPS = {
    "介绍类": [
        "介绍一下你自己",
        "你做过哪些和数据相关的项目？",
    ],
    "数据类": [
        "2018 年每月订单数，帮我画个图",
        "销量 top 5 的商品品类有哪些？",
    ],
    "综合类": [
        "你了解电商数据吗？给我看下月订单趋势并解读",
    ],
}


def _init_state() -> None:
    """Initialize session state for chat."""
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "last_result" not in st.session_state:
        st.session_state["last_result"] = None


def _render_quick_questions() -> None:
    """Render grouped quick questions."""
    for group_name, questions in EXAMPLE_GROUPS.items():
        st.caption(group_name)
        cols = st.columns(len(questions), gap="small")
        for col, question in zip(cols, questions):
            if col.button(
                question,
                use_container_width=True,
                key=f"example_{group_name}_{question}",
                type="secondary",
            ):
                st.session_state["_pending_input"] = question
                st.rerun()



def _render_welcome() -> None:
    """Render welcome message and quick actions when chat is empty."""
    if st.session_state["messages"]:
        return

    with st.container(border=True):
        st.markdown("#### 开始对话")
        st.caption("你可以提问个人经历、技术栈，或直接发起 Olist 数据分析问题。")
        st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)
        _render_quick_questions()



def render_chat() -> None:
    """Render chat history + input. Call agent on user input."""
    _init_state()

    pending = st.session_state.pop("_pending_input", None)

    if not st.session_state["messages"]:
        _render_welcome()

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("steps"):
                st.caption(f"执行步数: {msg['steps']}")

    prompt = pending or st.chat_input("输入问题，或点击上方快捷问题")

    if not prompt:
        return

    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("正在处理请求..."):
            try:
                result = run(prompt)
            except Exception as e:  # noqa: BLE001
                err_msg = (
                    f"执行失败：{e}\n\n"
                    "你可以换一种问法重试，或先用简短问题验证（例如：2018 年每月订单数）。"
                )
                st.error(err_msg)
                st.session_state["messages"].append(
                    {"role": "assistant", "content": err_msg}
                )
                return

        answer = result.get("answer", "")
        steps = result.get("steps", 0)
        trace = result.get("trace", [])

        st.markdown(answer)
        if trace:
            tools_used = " -> ".join(t["tool"] for t in trace)
            st.caption(f"{steps} 步 | {tools_used}")

        st.session_state["messages"].append(
            {"role": "assistant", "content": answer, "steps": steps}
        )
        st.session_state["last_result"] = result

    st.rerun()

