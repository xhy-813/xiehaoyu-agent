"""Unit tests for agent/tools/visualize.py — chart type selection heuristics."""

import pandas as pd
import pytest
from agent.tools.visualize import visualize, _is_time_col


class TestIsTimeCol:
    def test_datetime64_dtype(self):
        s = pd.Series(pd.to_datetime(["2020-01-01", "2020-01-02"]))
        assert _is_time_col("ts", s) is True

    def test_date_string_with_hint_name(self):
        s = pd.Series(["2020-01-01", "2020-01-02"])
        assert _is_time_col("order_date", s) is True

    def test_month_hint(self):
        s = pd.Series(["2020-01", "2020-02"])
        assert _is_time_col("month", s) is True

    def test_year_hint(self):
        s = pd.Series(["2020", "2021"])
        assert _is_time_col("year", s) is True

    def test_timestamp_hint(self):
        s = pd.Series(["2020-01-01 12:00:00"])
        assert _is_time_col("purchase_timestamp", s) is True

    def test_non_time_name(self):
        s = pd.Series(["hello", "world"])
        assert _is_time_col("product_name", s) is False


class TestVisualize:
    def test_empty_df_returns_table(self):
        df = pd.DataFrame()
        r = visualize(df)
        assert r.chart_type == "table"

    def test_single_numeric_indicator(self):
        df = pd.DataFrame({"total": [42]})
        r = visualize(df)
        assert r.chart_type == "indicator"

    def test_time_series_line(self):
        df = pd.DataFrame(
            {"month": ["2020-01", "2020-02", "2020-03"], "sales": [10, 20, 30]}
        )
        r = visualize(df, "monthly sales")
        assert r.chart_type == "line"

    def test_category_bar(self):
        df = pd.DataFrame(
            {"category": ["A", "B", "C"], "count": [30, 20, 10]}
        )
        r = visualize(df)
        assert r.chart_type == "bar"

    def test_two_numeric_scatter(self):
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
        r = visualize(df)
        assert r.chart_type == "scatter"

    def test_fallback_table_for_many_categories(self):
        df = pd.DataFrame(
            {"cat": [f"c{i}" for i in range(35)], "val": list(range(35))}
        )
        r = visualize(df)
        # >30 categories should fall back to table
        assert r.chart_type == "table"

    def test_multi_numeric_fallback(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
        r = visualize(df)
        # 3 numeric cols, no clear pattern → table
        assert r.chart_type == "table"