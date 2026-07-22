"""LLM natural-language interpretation of a query result.

给定 (question, sql, df)，让 LLM 输出 1~2 条中文业务洞察。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from openai import OpenAI

from configs.settings import settings


PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "explain.md"
PREVIEW_ROWS = 20


def _client() -> OpenAI:
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set in .env")
    return OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )


def _preview(df: pd.DataFrame, n: int = PREVIEW_ROWS) -> str:
    if df.empty:
        return "(空结果)"
    head = df.head(n)
    return head.to_string(index=False)


def explain_result(question: str, sql: str, df: pd.DataFrame) -> str:
    prompt = PROMPT_PATH.read_text(encoding="utf-8").format(
        question=question,
        sql=sql,
        preview=_preview(df),
    )
    client = _client()
    resp = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": "你是资深数据分析师，输出简洁中文洞察。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return (resp.choices[0].message.content or "").strip()
