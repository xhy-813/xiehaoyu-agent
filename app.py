"""Streamlit entry point: chat + trace panels."""

from __future__ import annotations

import streamlit as st

from configs.settings import settings
from ui.chat import render_chat
from ui.trace import render_chart, render_data, render_summary, render_trace


_CUSTOM_CSS = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent;}

section[data-testid="stMain"] > div {
    padding-top: 0.5rem;
}

html, body, [class*="css"] {
    font-family: "Inter", "Segoe UI", sans-serif;
}

[data-testid="stSidebar"] {
    background: #f8fafc;
    border-right: 1px solid #e2e8f0;
}

.block-container {
    max-width: 1400px;
}

h1, h2, h3 {
    color: #0f172a;
    letter-spacing: 0;
}

[data-testid="stChatMessage"] {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    background: #ffffff;
}

[data-testid="stChatMessageAvatarUser"] + [data-testid="stChatMessageContent"] {
    background: #eff6ff;
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
}

.stButton > button {
    min-height: 2.2rem;
    padding: 0.35rem 0.8rem;
    border-radius: 8px;
    border: 1px solid #cbd5e1;
    background: #f8fafc;
    color: #0f172a;
    font-weight: 500;
    font-size: 0.88rem;
    box-shadow: none;
}

.stButton > button:hover {
    background: #f1f5f9;
    border-color: #94a3b8;
}

.stButton > button[kind="primary"] {
    background: #2563eb;
    border-color: #2563eb;
    color: #ffffff;
}

.stButton > button[kind="primary"]:hover {
    background: #1d4ed8;
    border-color: #1d4ed8;
}

[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input {
    border-radius: 8px !important;
    border: 1px solid #cbd5e1 !important;
    background: #ffffff !important;
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    font-size: 0.92rem !important;
}

[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInput"] input::placeholder {
    color: #94a3b8 !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
}

@media (max-width: 900px) {
    .block-container {
        padding-left: 0.7rem;
        padding-right: 0.7rem;
        padding-top: 0.35rem;
    }

    [data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 0.65rem !important;
    }

    [data-testid="stHorizontalBlock"] > div {
        width: 100% !important;
        min-width: 0 !important;
        flex: 1 1 100% !important;
    }

    h1 {
        font-size: 1.45rem !important;
        line-height: 1.25 !important;
        margin-bottom: 0.25rem !important;
    }

    .stButton > button {
        min-height: 2.05rem;
        font-size: 0.84rem;
        padding: 0.32rem 0.65rem;
    }

    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInput"] input {
        font-size: 0.88rem !important;
        padding-top: 0.44rem !important;
        padding-bottom: 0.44rem !important;
    }

    .summary-metric {
        padding: 0.46rem 0.52rem;
    }

    .summary-label {
        font-size: 0.72rem;
    }

    .summary-value {
        font-size: 0.86rem;
    }
}



.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 0.45rem 0.8rem;
}

.result-shell {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.8rem;
    background: #ffffff;
}

.summary-metric {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 0.55rem 0.7rem;
    background: #f8fafc;
}

.summary-label {
    color: #64748b;
    font-size: 0.78rem;
    margin-bottom: 0.15rem;
}

.summary-value {
    color: #0f172a;
    font-size: 0.95rem;
    font-weight: 600;
}
</style>
"""


def _render_sidebar() -> None:
    """Render sidebar status and actions."""
    with st.sidebar:
        st.markdown("### Xiehaoyu-Agent")
        st.caption("Personal Agent + ChatBI")

        with st.container(border=True):
            st.markdown("**Session Status**")
            st.caption(f"Agent 步数上限: {settings.max_agent_steps}")
            st.caption(f"SQL 重试上限: {settings.sql_retry_max}")

        st.markdown("**对话操作**")
        if st.button("清空当前对话", use_container_width=True):
            st.session_state["messages"] = []
            st.session_state["last_result"] = None
            st.rerun()

        st.divider()
        st.caption("LangGraph · DeepSeek · ChromaDB · Streamlit")


def main() -> None:
    st.set_page_config(
        page_title="Xiehaoyu-Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(_CUSTOM_CSS, unsafe_allow_html=True)

    _render_sidebar()

    st.title("Xiehaoyu-Agent")
    st.caption("面向面试场景的个人智能体与数据问答工作台")

    col_chat, col_side = st.columns([5, 4], gap="medium")

    with col_chat:
        render_chat()

    with col_side:
        result = st.session_state.get("last_result")
        trace = result.get("trace", []) if result else []

        with st.expander("结果面板（可展开）", expanded=False):
            st.markdown('<div class="result-shell">', unsafe_allow_html=True)
            render_summary(trace)

            tab_data, tab_chart, tab_trace = st.tabs(["Data", "Chart", "Trace"])
            with tab_data:
                render_data(trace)
            with tab_chart:
                render_chart(trace)
            with tab_trace:
                render_trace(trace)
            st.markdown("</div>", unsafe_allow_html=True)



if __name__ == "__main__":
    main()

