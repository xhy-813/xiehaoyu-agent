"""Agent trace side panel (data / chart / trace)."""

from __future__ import annotations

import streamlit as st


_TOOL_ICONS = {
    "introduce_me": "📝",
    "query_data": "🔍",
    "visualize": "📈",
    "explain_result": "💡",
}


def _find_artifact(trace: list[dict], key: str) -> dict | None:
    """Find the last artifact containing *key* in trace."""
    for entry in reversed(trace):
        artifact = entry.get("artifact")
        if artifact and key in artifact:
            return artifact
    return None


def render_data(trace: list[dict]) -> None:
    """Display the latest query DataFrame."""
    artifact = _find_artifact(trace, "df")
    if artifact is None:
        st.markdown("### 📋 数据")
        st.info("暂无数据\n\n提问数据相关问题后，查询结果将在此展示。")
        return

    df = artifact["df"]
    sql = artifact.get("sql", "")
    if sql:
        st.caption("🔗 SQL")
        st.code(sql, language="sql")
    st.caption(f"📊 共 {len(df)} 行 × {len(df.columns)} 列")
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_chart(trace: list[dict]) -> None:
    """Display the latest Plotly figure."""
    artifact = _find_artifact(trace, "figure")
    if artifact is None:
        st.markdown("### 📈 图表")
        st.info("暂无图表\n\n提问需要可视化的问题后，图表将在此展示。")
        return

    fig = artifact["figure"]
    chart_type = artifact.get("chart_type", "")
    type_labels = {
        "indicator": "指标卡",
        "line": "折线图",
        "bar": "柱状图",
        "scatter": "散点图",
        "table": "表格",
    }
    label = type_labels.get(chart_type, chart_type)
    if label:
        st.caption(f"📊 图表类型: {label}")
    st.plotly_chart(fig, use_container_width=True)


def render_trace(trace: list[dict]) -> None:
    """Display execution trace as collapsible cards."""
    if not trace:
        st.markdown("### 🔍 执行轨迹")
        st.info("暂无轨迹\n\n提问后，Agent 的思考过程将在此展示。")
        return

    st.caption(f"📋 共 {len(trace)} 个工具调用")

    for i, entry in enumerate(trace, 1):
        tool = entry.get("tool", "?")
        args = entry.get("args", {})
        summary = entry.get("summary", "")
        icon = _TOOL_ICONS.get(tool, "🔧")
        arg_str = ", ".join(f"{k}={v!r}" for k, v in args.items()) if args else ""

        with st.expander(f"{icon} [{i}] {tool}({arg_str})", expanded=(i == len(trace))):
            st.text(summary)
