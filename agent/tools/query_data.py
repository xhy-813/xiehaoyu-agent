"""Text2SQL tool: LLM → validate → execute → retry on failure.

用法：
    from agent.tools.query_data import query_data
    result = query_data("2018 年每月订单数")
    print(result.sql, result.df.head())
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd
from openai import APIError, OpenAI
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from chatbi.few_shots import format_few_shots
from chatbi.schema import SCHEMA
from chatbi.validator import SQLValidationError, validate
from agent.llm_client import get_client
from configs.settings import settings


PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "text2sql.md"
DB_PATH = Path(__file__).resolve().parents[2] / "chatbi" / "data" / "olist.db"

# Module-level prompt cache
_PROMPT_TEMPLATE: str | None = None
_SYSTEM_ROLE: str | None = None


def _load_prompt() -> tuple[str, str]:
    """Parse text2sql.md into (system_role, user_template).

    The prompt file uses 【系统角色】 and 【安全规则】 section headers.
    Everything from 【安全规则】 onward is the user template.
    """
    global _PROMPT_TEMPLATE, _SYSTEM_ROLE
    if _PROMPT_TEMPLATE is None:
        raw = PROMPT_PATH.read_text(encoding="utf-8")
        # Extract system role: text between 【系统角色】 and 【安全规则】
        role_start = raw.find("【系统角色】")
        role_end = raw.find("【安全规则】")
        if role_start != -1 and role_end != -1:
            _SYSTEM_ROLE = raw[role_start + len("【系统角色】"):role_end].strip()
        else:
            _SYSTEM_ROLE = "你是资深数据分析师，只输出可执行的 SQLite SQL。"
        # User template: everything from 【安全规则】 onward
        _PROMPT_TEMPLATE = raw[role_end:].strip() if role_end != -1 else raw
    return _SYSTEM_ROLE, _PROMPT_TEMPLATE


@lru_cache(maxsize=1)
def _get_engine(db_path: str) -> Engine:
    """Return a cached SQLAlchemy engine (singleton per path)."""
    return create_engine(f"sqlite:///{db_path}")


@dataclass
class QueryResult:
    question: str
    sql: str
    df: pd.DataFrame
    attempts: int
    elapsed_ms: int
    trace: list[dict] = field(default_factory=list)  # 每轮 {sql, error}


def _build_prompt(question: str) -> tuple[str, str]:
    """Return (system_role, user_prompt) for the Text2SQL LLM call."""
    system_role, template = _load_prompt()
    user_prompt = template.format(
        schema=SCHEMA,
        few_shots=format_few_shots(),
        question=question,
    )
    return system_role, user_prompt


def _ask_llm(client: OpenAI, question: str, feedback: str | None = None) -> str:
    system_role, base_prompt = _build_prompt(question)
    messages: list[dict] = [
        {"role": "system", "content": system_role},
        {"role": "user", "content": base_prompt},
    ]
    if feedback:
        messages.append({"role": "user", "content": feedback})
    resp = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        temperature=settings.text2sql_temperature,
    )
    return resp.choices[0].message.content or ""


def _backoff_sleep(attempt: int, base_ms: int = 500) -> None:
    """Exponential backoff: 500ms, 1s, 2s, … capped at 5s."""
    delay = min(base_ms * (2 ** (attempt - 1)), 5000)
    time.sleep(delay / 1000)


def query_data(
    question: str,
    max_attempts: int | None = None,
    db_path: Path | None = None,
) -> QueryResult:
    max_attempts = max_attempts or settings.sql_retry_max
    engine = _get_engine(str(db_path or DB_PATH))
    client = get_client()

    trace: list[dict] = []
    feedback: str | None = None
    t0 = time.time()

    for attempt in range(1, max_attempts + 1):
        # ── LLM call ──
        try:
            raw = _ask_llm(client, question, feedback)
        except APIError as e:
            trace.append({"error": f"LLM API error: {e}"})
            if attempt < max_attempts:
                _backoff_sleep(attempt)
            feedback = (
                f"上一步调用 LLM 失败（API 错误）：{e}\n"
                "请重新输出一条合法的只读 SELECT SQL。"
            )
            continue
        except Exception as e:
            trace.append({"error": f"LLM call failed: {e}"})
            if attempt < max_attempts:
                _backoff_sleep(attempt)
            feedback = (
                f"上一步调用 LLM 失败：{e}\n"
                "请重新输出一条合法的只读 SELECT SQL。"
            )
            continue

        # ── Validation ──
        try:
            sql = validate(raw)
        except SQLValidationError as e:
            trace.append({"raw": raw, "error": f"validate: {e}"})
            if attempt < max_attempts:
                _backoff_sleep(attempt)
            feedback = (
                f"上一次输出未通过安全校验：{e}。"
                f"原文：\n{raw}\n请重新输出一条合法的只读 SELECT SQL。"
            )
            continue

        # ── Execution ──
        try:
            with engine.connect() as conn:
                df = pd.read_sql(text(sql), conn)
        except SQLAlchemyError as e:
            trace.append({"sql": sql, "error": f"execute: {e}"})
            if attempt < max_attempts:
                _backoff_sleep(attempt)
            feedback = (
                f"上一条 SQL 执行报错：{e}\nSQL：\n{sql}\n"
                "请根据错误信息修正后重新输出（同样只输出 SQL）。"
            )
            continue
        except Exception as e:
            trace.append({"sql": sql, "error": f"execute: {e}"})
            if attempt < max_attempts:
                _backoff_sleep(attempt)
            feedback = (
                f"上一条 SQL 执行报错：{e}\nSQL：\n{sql}\n"
                "请根据错误信息修正后重新输出（同样只输出 SQL）。"
            )
            continue

        elapsed_ms = int((time.time() - t0) * 1000)
        trace.append({"sql": sql, "rows": len(df)})
        return QueryResult(
            question=question,
            sql=sql,
            df=df,
            attempts=attempt,
            elapsed_ms=elapsed_ms,
            trace=trace,
        )

    raise RuntimeError(
        f"Text2SQL failed after {max_attempts} attempts. Trace: {trace}"
    )
