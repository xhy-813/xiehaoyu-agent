"""SQL safety validator.

规则：
- 只允许单条语句
- 只允许 SELECT / WITH ... SELECT
- 关键字黑名单（防注入 & 破坏）
"""

from __future__ import annotations

import re

import sqlparse


_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|ATTACH|"
    r"DETACH|PRAGMA|VACUUM|REINDEX|GRANT|REVOKE|EXPLAIN)\b",
    re.IGNORECASE,
)

# Regex for CTE-style statements that sqlparse reports as UNKNOWN.
# Matches "WITH ... SELECT" across multiple lines.
_CTE_SELECT_RE = re.compile(r"^\s*(WITH\b.+?\bSELECT\b)", re.IGNORECASE | re.DOTALL)

# Regex to strip SQL comments (line comments and block comments)
_COMMENT_RE = re.compile(
    r"--[^\n]*|/\*[\s\S]*?\*/",
    re.IGNORECASE,
)

# Regex to strip single-quoted string literals so the forbidden-keyword
# check doesn't false-positive on e.g. ``SELECT 'INSERT' AS action_type``
# Match single-quoted string literals, including SQL '' escape sequences
_STRING_LITERAL_RE = re.compile(r"'[^']*(?:''[^']*)*'")


class SQLValidationError(ValueError):
    """Raised when generated SQL fails safety checks."""


def clean_sql(sql: str) -> str:
    """Strip markdown fences / trailing whitespace commonly emitted by LLM."""
    s = sql.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s)
    return s.strip().rstrip(";") + ";"


def _strip_comments(sql: str) -> str:
    """Remove SQL line and block comments, replacing them with whitespace
    to preserve character positions."""
    return _COMMENT_RE.sub(" ", sql)


def _strip_string_literals(sql: str) -> str:
    """Remove single-quoted string literals for keyword-only checks."""
    return _STRING_LITERAL_RE.sub("", sql)


def validate(sql: str) -> str:
    """Return normalized SQL if safe; raise SQLValidationError otherwise."""
    s = clean_sql(sql)

    # Strip comments before checking structure (H14 fix)
    s_no_comments = _strip_comments(s)

    stmts = [x for x in sqlparse.parse(s_no_comments) if x.tokens and str(x).strip()]
    if len(stmts) != 1:
        raise SQLValidationError(f"expected 1 statement, got {len(stmts)}")

    stmt = stmts[0]
    kind = (stmt.get_type() or "").upper()

    if kind == "SELECT":
        pass  # straightforward SELECT — always ok
    elif kind == "UNKNOWN":
        # sqlparse reports CTEs (WITH ... SELECT) as UNKNOWN.
        # Only accept UNKNOWN when it is a CTE that opens with WITH and contains SELECT.
        if not _CTE_SELECT_RE.search(s_no_comments):
            raise SQLValidationError(
                f"UNKNOWN statement type is not a CTE SELECT — rejected"
            )
    else:
        raise SQLValidationError(f"only SELECT allowed, got {kind}")

    # Redundant safety net: ensure the statement starts with SELECT or WITH
    if not re.search(r"^\s*(WITH|SELECT)\b", s_no_comments, re.IGNORECASE):
        raise SQLValidationError("statement must start with SELECT or WITH")

    # Check forbidden keywords against the comment-stripped, string-literal-stripped
    # version to avoid false positives on string literals (H13 fix)
    s_check = _strip_string_literals(s_no_comments)
    if _FORBIDDEN.search(s_check):
        raise SQLValidationError("contains forbidden keyword")

    return s
