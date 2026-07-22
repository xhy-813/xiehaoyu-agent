"""Text2SQL tool: LLM → validate → execute → retry on failure.

用法：
    from agent.tools.query_data import query_data
    result = query_data("2018 年每月订单数")
    print(result.sql, result.df.head())
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from openai import OpenAI
from sqlalchemy import create_engine, text

from chatbi.few_shots import format_few_shots
from chatbi.schema import SCHEMA
from chatbi.validator import SQLValidationError, validate
from configs.settings import settings


PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "text2sql.md"
DB_PATH = Path(__file__).resolve().parents[2] / "chatbi" / "data" / "olist.db"


@dataclass
class QueryResult:
    question: str
    sql: str
    df: pd.DataFrame
    attempts: int
    elapsed_ms: int
    trace: list[dict] = field(default_factory=list)  # 每轮 {sql, error}


def _client() -> OpenAI:
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set in .env")
    return OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )


def _build_prompt(question: str) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.format(
        schema=SCHEMA,
        few_shots=format_few_shots(),
        question=question,
    )


def _ask_llm(client: OpenAI, prompt: str, feedback: str | None = None) -> str:
    messages: list[dict] = [
        {"role": "system", "content": "你是资深数据分析师，只输出可执行的 SQLite SQL。"},
        {"role": "user", "content": prompt},
    ]
    if feedback:
        messages.append({"role": "user", "content": feedback})
    resp = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=messages,
        temperature=0.0,
    )
    return resp.choices[0].message.content or ""


def query_data(
    question: str,
    max_attempts: int | None = None,
    db_path: Path | None = None,
) -> QueryResult:
    max_attempts = max_attempts or settings.sql_retry_max
    engine = create_engine(f"sqlite:///{db_path or DB_PATH}")
    client = _client()
    base_prompt = _build_prompt(question)

    trace: list[dict] = []
    feedback: str | None = None
    t0 = time.time()

    for attempt in range(1, max_attempts + 1):
        raw = _ask_llm(client, base_prompt, feedback)
        try:
            sql = validate(raw)
        except SQLValidationError as e:
            trace.append({"raw": raw, "error": f"validate: {e}"})
            feedback = (
                f"上一次输出未通过安全校验：{e}。"
                f"原文：\n{raw}\n请重新输出一条合法的只读 SELECT SQL。"
            )
            continue

        try:
            with engine.connect() as conn:
                df = pd.read_sql(text(sql), conn)
        except Exception as e:  # noqa: BLE001  DB errors are diverse
            trace.append({"sql": sql, "error": f"execute: {e}"})
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
