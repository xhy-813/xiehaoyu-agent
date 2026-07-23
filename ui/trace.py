"""Agent trace side panel (data / chart / trace)."""

from __future__ import annotations

import streamlit as st


_TOOL_ICONS = {
    "introduce_me": "doc",
    "query_data": "database",
    "visualize": "chart",
    "explain_result": "insight",
}


def _find_artifact(trace: list[dict], key: str) -> dict | None:
    """Find the last artifact containing *key* in trace."""
    for entry in reversed(trace):
        artifact = entry.get("artifact")
        if artifact and key in artifact:
            return artifact
    return None


def render_summary(trace: list[dict]) -> None:
    """Render compact result summary metrics."""
    df_artifact = _find_artifact(trace, "df")
    chart_artifact = _find_artifact(trace, "figure")
    steps = len(trace)

    if not (df_artifact or chart_artifact or steps):
        st.info("暂无结果。先在左侧发起一次提问。")
        return

    rows_cols = "--"
    if df_artifact is not None:
        df = df_artifact["df"]
        rows_cols = f"{len(df)} x {len(df.columns)}"

    chart_type = chart_artifact.get("chart_type", "--") if chart_artifact else "--"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            '<div class="summary-metric"><div class="summary-label">Rows x Cols</div>'
            f'<div class="summary-value">{rows_cols}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            '<div class="summary-metric"><div class="summary-label">Chart Type</div>'
            f'<div class="summary-value">{chart_type}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            '<div class="summary-metric"><div class="summary-label">Tool Steps</div>'
            f'<div class="summary-value">{steps}</div></div>',
            unsafe_allow_html=True,
        )


def render_data(trace: list[dict]) -> None:
    """Display the latest query DataFrame."""
    artifact = _find_artifact(trace, "df")
    if artifact is None:
        st.info("暂无数据。提问数据相关问题后，查询结果将在此展示。")
        return

    df = artifact["df"]
    sql = artifact.get("sql", "")

    if sql:
        with st.expander("查看 SQL", expanded=False):
            st.code(sql, language="sql")

    st.dataframe(df, use_container_width=True, hide_index=True)


def render_chart(trace: list[dict]) -> None:
    """Display the latest Plotly figure."""
    artifact = _find_artifact(trace, "figure")
    if artifact is None:
        st.info("暂无图表。提问需要可视化的问题后，图表将在此展示。")
        return

    fig = artifact["figure"]
    st.plotly_chart(fig, use_container_width=True)


def render_trace(trace: list[dict]) -> None:
    """Display execution trace as collapsible cards."""
    if not trace:
        st.info("暂无轨迹。提问后，Agent 的执行轨迹将在此展示。")
        return

    for i, entry in enumerate(trace, 1):
        tool = entry.get("tool", "unknown")
        args = entry.get("args", {})
        summary = entry.get("summary", "")
        tag = _TOOL_ICONS.get(tool, "tool")

        with st.expander(f"Step {i} · {tool} · {tag}", expanded=(i == len(trace))):
            st.caption("参数")
            if args:
                st.json(args)
            else:
                st.text("无")
            st.caption("输出摘要")
            st.write(summary or "无")

