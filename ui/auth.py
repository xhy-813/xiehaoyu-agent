"""Access-code gate + session hourly rate limit."""

from __future__ import annotations

import time

import streamlit as st

from configs.settings import settings


def check_access() -> bool:
    """Return True if user is authenticated. Renders login form if not."""
    if st.session_state.get("authenticated"):
        return True

    st.write("")
    st.write("")

    col_left, col_center, col_right = st.columns([1, 1.25, 1])
    with col_center:
        with st.container(border=True):
            st.markdown("### Xiehaoyu-Agent")
            st.caption("请输入访问码后继续")

            code = st.text_input(
                "访问码",
                type="password",
                placeholder="输入访问码",
                label_visibility="collapsed",
            )

            if st.button("进入工作台", type="primary", use_container_width=True):
                if code == settings.access_code:
                    st.session_state["authenticated"] = True
                    st.session_state["query_timestamps"] = []
                    st.rerun()
                else:
                    st.error("访问码错误，请重试")

            st.caption("如需访问码，请联系：谢浩宇")

    return False



def check_rate_limit() -> bool:
    """Return True if under hourly quota. Updates timestamp list on success."""
    now = time.time()
    timestamps = st.session_state.get("query_timestamps", [])
    # 清理 1 小时前的记录
    cutoff = now - 3600
    timestamps = [t for t in timestamps if t > cutoff]

    if len(timestamps) >= settings.session_hourly_quota:
        remaining_time = int(3600 - (now - timestamps[0]))
        minutes = max(1, remaining_time // 60)
        st.warning(
            f"⏳ 本小时提问次数已达上限（{settings.session_hourly_quota} 次），"
            f"约 {minutes} 分钟后重置，请稍后再试。"
        )
        return False

    timestamps.append(now)
    st.session_state["query_timestamps"] = timestamps
    return True
