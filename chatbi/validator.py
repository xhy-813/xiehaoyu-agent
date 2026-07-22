"""SQL safety validator: sqlparse-based syntax check, SELECT-only."""

import sqlparse


def is_safe_select(sql: str) -> bool:
    stmts = sqlparse.parse(sql)
    if len(stmts) != 1:
        return False
    return stmts[0].get_type().upper() == "SELECT"
