"""Text2SQL tool: LLM → validate → execute → retry on failure.

用法：
    from agent.tools.query_data import query_data
    result = query_data("2018 年每月订单数")
    print(result.sql, result.df.head())
"""

from __future__ import annotations

import asyncio
import sqlite3
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd
from openai import APIError, AsyncOpenAI
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from chatbi.few_shots import format_few_shots
from chatbi.schema import SCHEMA
from chatbi.validator import SQLValidationError, validate
from agent.llm_client import alogged_chat_create, get_async_client
from configs.settings import settings


PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "text2sql.md"
DB_PATH = Path(__file__).resolve().parents[2] / "chatbi" / "data" / "olist.db"

# Module-level prompt cache
_PROMPT_TEMPLATE: str | None = None
_SYSTEM_ROLE: str | None = None

# ── 808 审查 H4：执行层资源护栏（校验器防"写"，这里防"烧"）──
MAX_RESULT_ROWS = 10_000  # 结果集硬上限（超出截断）
STATEMENT_TIMEOUT_S = 15.0  # 单条 SQL 的 wall-clock 执行时限
_PROGRESS_TICKS = 10_000  # SQLite 进度回调的指令间隔（越小响应越快、开销越大）


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
    """Return a cached SQLAlchemy engine (singleton per path).

    以只读 URI 打开（808 审查 H4 纵深加固）：即使校验器被绕过，
    连接级也无法执行任何写操作。用 creator 直连以避免 SQLAlchemy
    URL 解析对 ``file:`` URI（尤其 Windows 盘符路径）的干扰。
    """
    uri = "file:" + Path(db_path).resolve().as_posix() + "?mode=ro"
    return create_engine(
        "sqlite://",
        creator=lambda: sqlite3.connect(uri, uri=True, check_same_thread=False),
    )


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


def _ask_llm_messages(question: str, feedback: str | None = None) -> list[dict]:
    """组装 Text2SQL 的消息序列（system 角色 + 用户 prompt + 可选错误反馈）。"""
    system_role, base_prompt = _build_prompt(question)
    messages: list[dict] = [
        {"role": "system", "content": system_role},
        {"role": "user", "content": base_prompt},
    ]
    if feedback:
        messages.append({"role": "user", "content": feedback})
    return messages


async def _ask_llm(client: AsyncOpenAI, question: str, feedback: str | None = None) -> str:
    resp = await alogged_chat_create(
        client,
        model=settings.deepseek_model,
        messages=_ask_llm_messages(question, feedback),
        temperature=settings.text2sql_temperature,
        caller="query_data",
    )
    return resp.choices[0].message.content or ""


def _backoff_delay_s(attempt: int, base_ms: int = 500) -> float:
    """Exponential backoff: 500ms, 1s, 2s, … capped at 5s."""
    return min(base_ms * (2 ** (attempt - 1)), 5000) / 1000


def _execute_sql(conn, sql: str) -> "pd.DataFrame":
    """Execute *sql* with a per-statement wall-clock guard (808 审查 H4)。

    SQLite 没有内建语句超时；progress handler 每执行约 ``_PROGRESS_TICKS``
    条 VM 指令回调一次，超时限返回 1 → sqlite3.OperationalError("interrupted")，
    由上层按执行失败进入重试/降级流程，而不是让线程被无限期占住
    （如无终止的递归以外的笛卡尔积慢查询）。
    """
    raw = conn.connection.driver_connection
    deadline = time.monotonic() + STATEMENT_TIMEOUT_S

    def _progress() -> int:
        return 1 if time.monotonic() > deadline else 0

    raw.set_progress_handler(_progress, _PROGRESS_TICKS)
    try:
        return pd.read_sql(text(sql), conn)
    finally:
        raw.set_progress_handler(None, 0)


def _run_sql(engine: Engine, sql: str) -> "pd.DataFrame":
    """同步执行包装（供 to_thread 调用）：连接 + 带护栏执行。"""
    with engine.connect() as conn:
        return _execute_sql(conn, sql)


async def query_data_async(
    question: str,
    max_attempts: int | None = None,
    db_path: Path | None = None,
    client: AsyncOpenAI | None = None,
) -> QueryResult:
    """Text2SQL 异步核心（808 审查 M1）。

    LLM 调用为真异步（取消即中止 HTTP 请求，不再断连后继续计费）；
    SQL 执行经 to_thread 隔离，避免阻塞事件循环。
    """
    max_attempts = max_attempts or settings.sql_retry_max
    engine = _get_engine(str(db_path or DB_PATH))
    owns_client = client is None
    llm = client or get_async_client()

    trace: list[dict] = []
    feedback: str | None = None
    t0 = time.time()

    try:
        for attempt in range(1, max_attempts + 1):
            # ── LLM call ──
            try:
                raw = await _ask_llm(llm, question, feedback)
            except APIError as e:
                trace.append({"error": f"LLM API error: {e}"})
                if attempt < max_attempts:
                    await asyncio.sleep(_backoff_delay_s(attempt))
                feedback = (
                    f"上一步调用 LLM 失败（API 错误）：{e}\n"
                    "请重新输出一条合法的只读 SELECT SQL。"
                )
                continue
            except Exception as e:
                trace.append({"error": f"LLM call failed: {e}"})
                if attempt < max_attempts:
                    await asyncio.sleep(_backoff_delay_s(attempt))
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
                    await asyncio.sleep(_backoff_delay_s(attempt))
                feedback = (
                    f"上一次输出未通过安全校验：{e}。"
                    f"原文：\n{raw}\n请重新输出一条合法的只读 SELECT SQL。"
                )
                continue

            # ── Execution ──
            try:
                df = await asyncio.to_thread(_run_sql, engine, sql)
            except SQLAlchemyError as e:
                trace.append({"sql": sql, "error": f"execute: {e}"})
                if attempt < max_attempts:
                    await asyncio.sleep(_backoff_delay_s(attempt))
                feedback = (
                    f"上一条 SQL 执行报错：{e}\nSQL：\n{sql}\n"
                    "请根据错误信息修正后重新输出（同样只输出 SQL）。"
                )
                continue
            except Exception as e:
                trace.append({"sql": sql, "error": f"execute: {e}"})
                if attempt < max_attempts:
                    await asyncio.sleep(_backoff_delay_s(attempt))
                feedback = (
                    f"上一条 SQL 执行报错：{e}\nSQL：\n{sql}\n"
                    "请根据错误信息修正后重新输出（同样只输出 SQL）。"
                )
                continue

            if len(df) > MAX_RESULT_ROWS:
                df = df.head(MAX_RESULT_ROWS)
                trace.append({"sql": sql, "note": f"结果截断至 {MAX_RESULT_ROWS} 行"})

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
    finally:
        if owns_client:
            await llm.close()  # 自建客户端随用随关，避免 asyncio.run 短循环下的连接噪音


def query_data(
    question: str,
    max_attempts: int | None = None,
    db_path: Path | None = None,
) -> QueryResult:
    """同步门面（评测脚本 / smoke 用）。异步链路请直接 await query_data_async。"""
    return asyncio.run(query_data_async(question, max_attempts, db_path))
