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
            validate("-- comment\nSELECT 1;")