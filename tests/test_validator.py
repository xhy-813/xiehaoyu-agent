"""Unit tests for chatbi/validator.py — SQL safety validation."""

import pytest
from chatbi.validator import clean_sql, validate, SQLValidationError


class TestCleanSql:
    def test_strips_trailing_semicolons(self):
        assert clean_sql("SELECT 1;") == "SELECT 1;"

    def test_strips_markdown_code_block(self):
        result = clean_sql("```sql\nSELECT 1;\n```")
        assert result == "SELECT 1;"

    def test_strips_plain_code_block(self):
        result = clean_sql("```\nSELECT 1;\n```")
        assert result == "SELECT 1;"

    def test_handles_no_semicolon(self):
        assert clean_sql("SELECT 1") == "SELECT 1;"

    def test_handles_whitespace(self):
        assert clean_sql("  SELECT 1;  ") == "SELECT 1;"


class TestValidate:
    def test_valid_simple_select(self):
        assert validate("SELECT 1;") == "SELECT 1;"

    def test_valid_select_with_columns(self):
        sql = validate("SELECT col1, col2 FROM table1;")
        assert "SELECT" in sql

    def test_valid_with_cte(self):
        result = validate("WITH t AS (SELECT 1 AS n) SELECT n FROM t;")
        assert result.startswith("WITH")

    def test_valid_select_with_joins(self):
        result = validate(
            "SELECT * FROM orders o JOIN customers c ON o.customer_id = c.customer_id;"
        )
        assert "JOIN" in result

    def test_rejects_recursive_cte(self):
        """808 审查 H4：递归 CTE 可无终止计算，一律拒绝。"""
        with pytest.raises(SQLValidationError, match="recursive"):
            validate(
                "WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT n+1 FROM r) "
                "SELECT COUNT(*) FROM r;"
            )

    def test_rejects_pragma_function_form(self):
        """PRAGMA 不匹配 pragma_table_info（下划线是词字符），函数形式单独拦截。"""
        with pytest.raises(SQLValidationError, match="forbidden function"):
            validate("SELECT * FROM pragma_table_info('orders');")

    def test_rejects_readfile_function(self):
        with pytest.raises(SQLValidationError, match="forbidden function"):
            validate("SELECT readfile('/etc/passwd');")

    def test_rejects_load_extension_function(self):
        with pytest.raises(SQLValidationError, match="forbidden function"):
            validate("SELECT load_extension('evil.so');")

    def test_normal_cte_still_allowed(self):
        result = validate(
            "WITH monthly AS (SELECT strftime('%Y-%m', ts) AS m FROM t) "
            "SELECT m FROM monthly;"
        )
        assert result.startswith("WITH")

    def test_rejects_insert(self):
        with pytest.raises(SQLValidationError):
            validate("INSERT INTO t VALUES (1);")

    def test_rejects_update(self):
        with pytest.raises(SQLValidationError):
            validate("UPDATE t SET x = 1;")

    def test_rejects_delete(self):
        with pytest.raises(SQLValidationError):
            validate("DELETE FROM t;")

    def test_rejects_drop(self):
        with pytest.raises(SQLValidationError):
            validate("DROP TABLE t;")

    def test_rejects_alter(self):
        with pytest.raises(SQLValidationError):
            validate("ALTER TABLE t ADD COLUMN x INT;")

    def test_rejects_create(self):
        with pytest.raises(SQLValidationError):
            validate("CREATE TABLE t (x INT);")

    def test_rejects_multiple_statements(self):
        with pytest.raises(SQLValidationError):
            validate("SELECT 1; SELECT 2;")

    def test_rejects_attached_database(self):
        with pytest.raises(SQLValidationError):
            validate("ATTACH DATABASE 'x.db' AS x;")

    def test_rejects_pragma(self):
        with pytest.raises(SQLValidationError):
            validate("PRAGMA table_info(t);")

    def test_rejects_statement_not_starting_with_select(self):
        with pytest.raises(SQLValidationError):
            validate("EXPLAIN QUERY PLAN SELECT 1;")

    def test_accepts_sql_with_leading_comment(self):
        """H14: comments are stripped before structure check."""
        result = validate("-- comment\nSELECT 1;")
        assert "SELECT 1" in result

    def test_accepts_sql_with_block_comment(self):
        """H14: block comments are stripped before structure check."""
        result = validate("/* block comment */\nSELECT 1;")
        assert "SELECT 1" in result

    def test_accepts_select_with_forbidden_keyword_in_string(self):
        """H13: forbidden keywords inside string literals are not rejected."""
        result = validate("SELECT 'INSERT' AS action_type;")
        assert "action_type" in result

    def test_accepts_select_with_drop_table_in_string(self):
        """H13: forbidden keywords inside string literals are not rejected."""
        result = validate("SELECT 'DROP TABLE' AS cmd;")
        assert "cmd" in result

    def test_rejects_explain(self):
        """C1: EXPLAIN is now in the forbidden list."""
        with pytest.raises(SQLValidationError):
            validate("EXPLAIN SELECT 1;")

    def test_rejects_explain_query_plan(self):
        """C1: EXPLAIN QUERY PLAN is also rejected."""
        with pytest.raises(SQLValidationError):
            validate("EXPLAIN QUERY PLAN SELECT 1;")

    def test_accepts_union(self):
        """UNION is a valid SQLite read-only construct."""
        result = validate("SELECT 1 UNION SELECT 2;")
        assert "UNION" in result

    def test_rejects_subquery_injection(self):
        """DROP inside a subquery in comments should be rejected."""
        with pytest.raises(SQLValidationError):
            validate("SELECT 1; DROP TABLE orders;")

    def test_accepts_window_function(self):
        result = validate(
            "SELECT customer_id, ROW_NUMBER() OVER (PARTITION BY customer_state ORDER BY order_purchase_timestamp) AS rn FROM orders;"
        )
        assert "ROW_NUMBER" in result

    def test_accepts_group_by_with_having(self):
        result = validate(
            "SELECT customer_state, COUNT(*) AS cnt FROM customers GROUP BY customer_state HAVING cnt > 10;"
        )
        assert "HAVING" in result