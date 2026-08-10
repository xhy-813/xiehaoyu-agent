"""Text2SQL pipeline tests: prompt building, validation, retry logic, and
end-to-end queries against a file-backed SQLite database.

These tests verify the core pipeline in ``agent/tools/query_data.py``
without calling the real LLM API.  Mock LLM responses are injected so
that validation, retry, and error-handling paths are exercised deterministically.
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from agent.tools.query_data import (
    QueryResult,
    _build_prompt,
    _get_engine,
    query_data,
)
from chatbi.validator import SQLValidationError


# ── Fixtures ──────────────────────────────────────────────────


@pytest.fixture
def test_db() -> str:
    """Create a file-backed SQLite database with a minimal Olist-like schema.

    Returns the path to the .db file.  Uses a real file because SQLAlchemy's
    ``sqlite:///`` driver resolves ``:memory:`` differently from the stdlib
    ``sqlite3`` module.
    """
    import os
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE customers (
            customer_id TEXT,
            customer_unique_id TEXT,
            customer_city TEXT,
            customer_state TEXT
        );
        CREATE TABLE orders (
            order_id TEXT,
            customer_id TEXT,
            order_status TEXT,
            order_purchase_timestamp TEXT
        );
        CREATE TABLE order_items (
            order_id TEXT,
            order_item_id INTEGER,
            product_id TEXT,
            price REAL
        );
        CREATE TABLE products (
            product_id TEXT,
            product_category_name TEXT
        );

        INSERT INTO customers VALUES
            ('c1', 'cu1', 'Sao Paulo', 'SP'),
            ('c2', 'cu2', 'Rio', 'RJ'),
            ('c3', 'cu1', 'Sao Paulo', 'SP');

        INSERT INTO orders VALUES
            ('o1', 'c1', 'delivered', '2018-01-15 10:00:00'),
            ('o2', 'c2', 'delivered', '2018-02-20 10:00:00'),
            ('o3', 'c3', 'shipped',   '2018-03-10 10:00:00');

        INSERT INTO order_items VALUES
            ('o1', 1, 'p1', 100.0),
            ('o1', 2, 'p2', 50.0),
            ('o2', 1, 'p1', 200.0);

        INSERT INTO products VALUES
            ('p1', 'electronics'),
            ('p2', 'books');
    """)
    conn.close()
    yield path
    # Cleanup: clear the engine cache + remove the temp file
    _get_engine.cache_clear()
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture(autouse=True)
def clear_engine_cache():
    """Ensure the cached SQLAlchemy engine is cleared between tests."""
    _get_engine.cache_clear()
    yield
    _get_engine.cache_clear()


@pytest.fixture
def mock_client() -> MagicMock:
    """Return a MagicMock that behaves like an AsyncOpenAI client (M1)."""
    m = MagicMock()
    m.chat.completions.create = AsyncMock()
    m.close = AsyncMock()  # query_data_async 的 finally 会 await close()
    return m


# ── _build_prompt tests ───────────────────────────────────────


class TestBuildPrompt:
    def test_includes_schema(self):
        system_role, user_prompt = _build_prompt("2018 年每月订单数")
        assert "customers" in user_prompt
        assert "orders" in user_prompt
        assert "order_items" in user_prompt

    def test_includes_few_shots(self):
        system_role, user_prompt = _build_prompt("2018 年每月订单数")
        assert "2018 年每月的订单数" in user_prompt
        assert "strftime" in user_prompt

    def test_includes_user_question(self):
        system_role, user_prompt = _build_prompt("2018 年每月订单数")
        assert "2018 年每月订单数" in user_prompt

    def test_includes_quality_rules(self):
        system_role, user_prompt = _build_prompt("任意问题")
        assert "SQL 编写规范" in user_prompt
        assert "反面示例" in user_prompt


# ── query_data – success path ─────────────────────────────────


class TestQueryDataSuccess:
    def test_single_attempt_success(self, test_db, mock_client):
        """One-shot: LLM returns valid SQL, DB executes it, result returned."""
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="SELECT COUNT(*) AS cnt FROM orders;"))]
        )

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            result = query_data("how many orders?", db_path=Path(test_db))

        assert isinstance(result, QueryResult)
        assert result.attempts == 1
        assert result.df.iloc[0, 0] == 3
        assert len(result.trace) == 1
        assert result.trace[0]["rows"] == 1

    def test_result_contains_sql(self, test_db, mock_client):
        sql = "SELECT customer_state, COUNT(*) AS cnt FROM customers GROUP BY 1 ORDER BY 2 DESC;"
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=sql))]
        )

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            result = query_data("state distribution", db_path=Path(test_db))

        assert result.sql.rstrip(";").strip() == sql.rstrip(";").strip()
        assert result.question == "state distribution"

    def test_df_has_correct_shape(self, test_db, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="SELECT * FROM orders;"))]
        )

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            result = query_data("all orders", db_path=Path(test_db))

        assert result.df.shape == (3, 4)


# ── query_data – retry on validation error ────────────────────


class TestQueryDataRetryValidation:
    def test_retry_after_sql_validation_error(self, test_db, mock_client):
        """First LLM call returns forbidden SQL, second returns valid SQL."""
        mock_client.chat.completions.create.side_effect = [
            MagicMock(choices=[MagicMock(message=MagicMock(content="DROP TABLE orders;"))]),
            MagicMock(choices=[MagicMock(message=MagicMock(content="SELECT COUNT(*) FROM orders;"))]),
        ]

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            result = query_data("test", db_path=Path(test_db))

        assert result.attempts == 2
        assert result.df.iloc[0, 0] == 3
        # trace should have 2 entries: first a validation error, second success
        assert len(result.trace) == 2
        assert "validate" in result.trace[0]["error"]

    def test_retry_after_execution_error(self, test_db, mock_client):
        """First LLM generates valid SQL but it fails at execution, second succeeds."""
        mock_client.chat.completions.create.side_effect = [
            MagicMock(choices=[MagicMock(message=MagicMock(content="SELECT * FROM nonexistent_table;"))]),
            MagicMock(choices=[MagicMock(message=MagicMock(content="SELECT COUNT(*) FROM orders;"))]),
        ]

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            result = query_data("test", db_path=Path(test_db))

        assert result.attempts == 2
        assert result.df.iloc[0, 0] == 3
        assert "execute" in result.trace[0]["error"]


# ── query_data – retry exhausted ──────────────────────────────


class TestQueryDataRetryExhausted:
    def test_raises_runtime_error_after_max_attempts(self, test_db, mock_client):
        """Every LLM response fails validation — should raise RuntimeError."""
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="INSERT INTO orders VALUES (1);"))]
        )

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Text2SQL failed"):
                query_data("test", max_attempts=2, db_path=Path(test_db))

    def test_trace_captures_all_attempts(self, test_db, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="INSERT INTO orders VALUES (1);"))]
        )

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            try:
                query_data("test", max_attempts=3, db_path=Path(test_db))
            except RuntimeError as e:
                trace = e.args[0]  # trace is embedded in the error message
                assert "Trace:" in trace


# ── query_data – LLM API error handling ───────────────────────


class TestQueryDataLLMErrors:
    def test_retry_after_llm_api_error(self, test_db, mock_client):
        """First LLM call hits an API error, second succeeds."""
        mock_client.chat.completions.create.side_effect = [
            Exception("API rate limit exceeded"),
            MagicMock(choices=[MagicMock(message=MagicMock(content="SELECT COUNT(*) FROM orders;"))]),
        ]

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            result = query_data("test", max_attempts=3, db_path=Path(test_db))

        assert result.attempts == 2
        assert "LLM call failed" in result.trace[0]["error"]

    def test_llm_returns_empty_response(self, test_db, mock_client):
        """LLM returns empty string — should fail validation and retry."""
        mock_client.chat.completions.create.side_effect = [
            MagicMock(choices=[MagicMock(message=MagicMock(content=""))]),
            MagicMock(choices=[MagicMock(message=MagicMock(content="SELECT COUNT(*) FROM orders;"))]),
        ]

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            result = query_data("test", max_attempts=3, db_path=Path(test_db))

        assert result.attempts == 2


# ── query_data – CTE and complex SQL ──────────────────────────


class TestQueryDataComplexSQL:
    def test_cte_query_passes_validation(self, test_db, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=(
                "WITH delivered AS ("
                "  SELECT customer_id FROM orders WHERE order_status = 'delivered'"
                ") SELECT COUNT(*) FROM delivered;"
            )))]
        )

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            result = query_data("delivered count", db_path=Path(test_db))

        assert result.attempts == 1
        assert result.df.iloc[0, 0] == 2

    def test_aggregation_query(self, test_db, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=(
                "SELECT order_status, COUNT(*) AS cnt "
                "FROM orders GROUP BY order_status ORDER BY cnt DESC;"
            )))]
        )

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            result = query_data("status breakdown", db_path=Path(test_db))

        assert result.attempts == 1
        assert len(result.df) == 2  # delivered + shipped


# ── query_data – elapsed timing ───────────────────────────────


class TestQueryDataTiming:
    def test_elapsed_ms_is_positive(self, test_db, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="SELECT 1;"))]
        )

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            result = query_data("test", db_path=Path(test_db))

        assert result.elapsed_ms > 0


# ── query_data – edge cases ───────────────────────────────────


class TestQueryDataEdgeCases:
    def test_empty_result_set(self, test_db, mock_client):
        """Query returns 0 rows — should still succeed."""
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=(
                "SELECT * FROM orders WHERE order_status = 'canceled';"
            )))]
        )

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            result = query_data("canceled orders", db_path=Path(test_db))

        assert result.attempts == 1
        assert len(result.df) == 0

    def test_question_with_special_characters(self, test_db, mock_client):
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="SELECT COUNT(*) FROM orders;"))]
        )

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            result = query_data("2018年 订单数? (所有)", db_path=Path(test_db))

        assert result.attempts == 1


# ── SQLValidationError integration ────────────────────────────


class TestSQLValidationErrorIntegration:
    def test_validation_error_has_message(self):
        err = SQLValidationError("only SELECT allowed, got INSERT")
        assert "INSERT" in str(err)

    def test_validation_error_is_value_error(self):
        assert issubclass(SQLValidationError, ValueError)


# ── 808 审查 H4：执行层资源护栏 ────────────────────────────


class TestExecutionGuardrails:
    def test_statement_timeout_aborts_long_query(self, test_db, mock_client, monkeypatch):
        """语句超时：超过 STATEMENT_TIMEOUT_S 的查询被 progress handler 中断，
        按执行失败处理（重试耗尽后 RuntimeError），而非线程被永久占住。"""
        import agent.tools.query_data as qd

        monkeypatch.setattr(qd, "STATEMENT_TIMEOUT_S", -1)  # 到期即中止
        monkeypatch.setattr(qd, "_PROGRESS_TICKS", 1)  # 每条指令都回调 → 必然触发
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(
                content="SELECT COUNT(*) FROM orders a, orders b, orders c;"
            ))]
        )

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            with pytest.raises(RuntimeError, match="Text2SQL failed"):
                query_data("test", max_attempts=1, db_path=Path(test_db))

    def test_result_rows_capped(self, test_db, mock_client, monkeypatch):
        """结果集行数硬上限：超出截断。"""
        import agent.tools.query_data as qd

        monkeypatch.setattr(qd, "MAX_RESULT_ROWS", 2)
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="SELECT * FROM orders;"))]
        )

        with patch("agent.tools.query_data.get_async_client", return_value=mock_client):
            result = query_data("all orders", db_path=Path(test_db))

        assert len(result.df) == 2  # 原表 3 行，截断至 2

    def test_engine_is_read_only(self, test_db, mock_client):
        """只读模式：即使绕过校验器，连接级写操作也被拒绝。"""
        import agent.tools.query_data as qd

        engine = qd._get_engine(test_db)
        from sqlalchemy import text as sa_text
        from sqlalchemy.exc import SQLAlchemyError

        with engine.connect() as conn:
            with pytest.raises(SQLAlchemyError):
                conn.execute(sa_text("CREATE TABLE hacked (id INTEGER)"))
