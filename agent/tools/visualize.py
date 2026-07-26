"""Auto-visualization: pick a Plotly figure based on df shape/dtypes.

规则（按优先级）：
1. 1 行 1 列 数值 → 指标卡（Indicator）
2. 只有 1 个时间列 + 1~N 个数值列 → 折线图
3. 1 个分类列 + 1 个数值列（分类数 ≤ 30）→ 柱状图（按数值降序）
4. 恰好 2 个数值列 → 散点图
5. 兜底 → 表格
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


TIME_HINT = ("date", "time", "month", "year", "day", "timestamp", "ts", "dt", "created_at", "updated_at")


@dataclass
class VizResult:
    chart_type: str  # 'indicator' | 'line' | 'bar' | 'scatter' | 'table'
    figure: go.Figure
    reason: str


def _is_time_col(name: str, series: pd.Series) -> bool:
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    lname = name.lower()
    if not any(h in lname for h in TIME_HINT):
        return False
    # 尝试宽松解析
    try:
        pd.to_datetime(series.head(20), errors="raise")
        return True
    except (ValueError, TypeError):
        return False


def _table_fig(df: pd.DataFrame) -> go.Figure:
    return go.Figure(
        data=[
            go.Table(
                header=dict(values=list(df.columns), fill_color="#eef", align="left"),
                cells=dict(
                    values=[df[c].astype(str).tolist() for c in df.columns],
                    align="left",
                ),
            )
        ]
    )


def visualize(df: pd.DataFrame, question: str = "") -> VizResult:
    if df is None or df.empty:
        return VizResult("table", _table_fig(pd.DataFrame({"info": ["无数据"]})), "empty df")

    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    other_cols = [c for c in df.columns if c not in numeric_cols]
    time_cols = [c for c in df.columns if _is_time_col(c, df[c])]

    # 1) 单数值指标卡
    if df.shape == (1, 1) and numeric_cols:
        val = df.iloc[0, 0]
        fig = go.Figure(
            go.Indicator(
                mode="number",
                value=float(val),
                title={"text": question or df.columns[0]},
            )
        )
        return VizResult("indicator", fig, "1x1 numeric")

    # 2) 时间序列
    if time_cols and numeric_cols:
        t = time_cols[0]
        d = df.copy()
        d[t] = pd.to_datetime(d[t], errors="coerce")
        d = d.sort_values(t)
        ycols = [c for c in numeric_cols if c != t]
        fig = px.line(d, x=t, y=ycols, markers=True, title=question or None)
        return VizResult("line", fig, f"time series on {t}")

    # 3) 分类 + 数值 柱状图
    if len(other_cols) == 1 and len(numeric_cols) == 1:
        cat, val = other_cols[0], numeric_cols[0]
        if df[cat].nunique() <= 30:
            d = df.sort_values(val, ascending=False)
            fig = px.bar(d, x=cat, y=val, title=question or None)
            return VizResult("bar", fig, "category + numeric")

    # 4) 两个数值列 → 散点
    if len(numeric_cols) == 2 and not other_cols:
        x, y = numeric_cols
        fig = px.scatter(df, x=x, y=y, title=question or None)
        return VizResult("scatter", fig, "two numeric cols")

    # 5) 兜底
    return VizResult("table", _table_fig(df), "fallback table")


def to_dict(result: VizResult) -> dict[str, Any]:
    """Serialize for storage / LLM context."""
    return {
        "chart_type": result.chart_type,
        "reason": result.reason,
        "figure": result.figure.to_dict(),
    }
