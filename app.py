"""Streamlit entry point: auth gate + chat + trace panels."""

from __future__ import annotations

import time

import streamlit as st

from configs.settings import settings
from ui.auth import check_access
from ui.chat import render_chat
from ui.trace import render_chart, render_data, render_trace


_CUSTOM_CSS = """
<style>
/* 隐藏默认 header 和 footer */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}

/* 主容器宽度 */
section[data-testid="stMain"] > div {
    padding-top: 1rem;
}

/* 标题样式 */
h1 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
}

/* Tab 样式 */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    padding: 8px 16px;
    border-radius: 8px 8px 0 0;
}

/* 聊天消息圆角 */
[data-testid="stChatMessage"] {
    border-radius: 12px;
    padding: 12px 16px;
}

/* 侧边栏 */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
}

/* 按钮样式 */
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
}

/* expander 样式 */
.streamlit-expanderHeader {
    font-size: 14px;
    font-weight: 500;
}
</style>
"""


def _render_sidebar() -> None:
    """渲染侧边栏：用户状态、剩余配额、清除对话。"""
    with st.sidebar:
        st.markdown("### 🤖 Xiehaoyu-Agent")

        # 配额信息
        now = time.time()
        timestamps = st.session_state.get("query_timestamps", [])
        cutoff = now - 3600
        used = len([t for t in timestamps if t > cutoff])
        remaining = settings.session_hourly_quota - used

        st.metric("剩余配额", f"{remaining} / {settings.session_hourly_quota}", "次/小时")
        st.caption(f"Agent 最大步数: {settings.max_agent_steps} ｜ SQL 重试: {settings.sql_retry_max}")

        st.divider()

        # 对话管理
        st.markdown("#### 对话管理")
        if st.button("🗑️ 清除对话", use_container_width=True):
            st.session_state["messages"] = []
            st.session_state["last_result"] = None
            st.rerun()

        st.divider()

        # 关于
        st.caption(
            "基于 LangGraph + DeepSeek + ChromaDB\n\n"
            "© 2026 谢浩宇"
        )


def main() -> None:
    st.set_page_config(
        page_title="Xiehaoyu-Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)

    # 访问码校验
    if not check_access():
        return

    # 侧边栏
    _render_sidebar()

    # 主页标题
    st.markdown("# 🤖 Xiehaoyu-Agent")
    st.caption("基于 LLM Agent 的个人智能体与 ChatBI 系统 ｜ 问我任何关于谢浩宇或 Olist 电商数据的问题")

    # 左右分栏
    col_chat, col_side = st.columns([3, 2])

    with col_chat:
        render_chat()

    with col_side:
        st.markdown("#### 📊 结果面板")
        tab_data, tab_chart, tab_trace = st.tabs(["📋 Data", "📈 Chart", "🔍 Trace"])
        result = st.session_state.get("last_result")

        if result:
            trace = result.get("trace", [])
            with tab_data:
                render_data(trace)
            with tab_chart:
                render_chart(trace)
            with tab_trace:
                render_trace(trace)
        else:
            with tab_data:
                st.markdown("### 📋 数据")
                st.info("暂无数据\n\n提问数据相关问题后，查询结果将在此展示。")
            with tab_chart:
                st.markdown("### 📈 图表")
                st.info("暂无图表\n\n提问需要可视化的问题后，图表将在此展示。")
            with tab_trace:
                st.markdown("### 🔍 执行轨迹")
                st.info("暂无轨迹\n\n提问后，Agent 的思考过程将在此展示。")


if __name__ == "__main__":
    main()
