"""LLM natural-language interpretation of a query result.

给定 (question, sql, df)，让 LLM 输出 3~5 条中文业务洞察。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from openai import OpenAI

from agent.llm_client import get_client
from configs.settings import settings


PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "explain.md"
PREVIEW_ROWS = 20

# Module-level prompt cache
_SYSTEM_ROLE: str | None = None
_USER_TEMPLATE: str | None = None


def _load_prompt() -> tuple[str, str]:
    """Parse explain.md into (system_role, user_template)."""
    global _SYSTEM_ROLE, _USER_TEMPLATE
    if _SYSTEM_ROLE is None:
        raw = PROMPT_PATH.read_text(encoding="utf-8")
        role_start = raw.find("【系统角色】")
        role_end = raw.find("【用户问题】")
        if role_start != -1 and role_end != -1:
            _SYSTEM_ROLE = raw[role_start + len("【系统角色】"):role_end].strip()
        else:
            _SYSTEM_ROLE = "你是资深数据分析师，输出简洁中文洞察。"
        _USER_TEMPLATE = raw[role_end:].strip() if role_end != -1 else raw
    return _SYSTEM_ROLE, _USER_TEMPLATE


def _preview(df: pd.DataFrame, n: int = PREVIEW_ROWS) -> str:
    if df.empty:
        return "(空结果)"
    head = df.head(n)
    return head.to_string(index=False)


def explain_result(question: str, sql: str, df: pd.DataFrame) -> str:
    system_role, user_template = _load_prompt()
    prompt = user_template.format(
        question=question,
        sql=sql,
        preview=_preview(df),
    )
    client = get_client()
    try:
        resp = client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt},
            ],
            temperature=settings.explain_temperature,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        raise RuntimeError(f"explain_result LLM call failed: {exc}") from exc
