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
    r"DETACH|PRAGMA|VACUUM|REINDEX|GRANT|REVOKE)\b",
    re.IGNORECASE,
)


class SQLValidationError(ValueError):
    """Raised when generated SQL fails safety checks."""


def clean_sql(sql: str) -> str:
    """Strip markdown fences / trailing whitespace commonly emitted by LLM."""
    s = sql.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s)
    return s.strip().rstrip(";") + ";"


def validate(sql: str) -> str:
    """Return normalized SQL if safe; raise SQLValidationError otherwise."""
    s = clean_sql(sql)

    stmts = [x for x in sqlparse.parse(s) if x.tokens and str(x).strip()]
    if len(stmts) != 1:
        raise SQLValidationError(f"expected 1 statement, got {len(stmts)}")

    stmt = stmts[0]
    kind = (stmt.get_type() or "").upper()
    if kind not in {"SELECT", "UNKNOWN"}:  # sqlparse 对 WITH ... SELECT 报 UNKNOWN
        raise SQLValidationError(f"only SELECT allowed, got {kind}")

    if not re.search(r"^\s*(WITH|SELECT)\b", s, re.IGNORECASE):
        raise SQLValidationError("statement must start with SELECT or WITH")

    if _FORBIDDEN.search(s):
        raise SQLValidationError("contains forbidden keyword")

    return s
