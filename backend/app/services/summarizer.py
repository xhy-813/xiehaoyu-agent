"""触发式摘要 + 会话标题生成（设计文档 §6）。

摘要触发条件：总轮数 > MEMORY_SUMMARY_TRIGGER_TURNS 且
距上次摘要的新增轮数 > MEMORY_SUMMARY_MIN_NEW_TURNS。
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from agent.llm_client import get_client
from agent.sanitize import sanitize_history
from backend.app.services import session_store
from configs.settings import settings

logger = logging.getLogger(__name__)

SUMMARY_PROMPT_PATH = Path(__file__).resolve().parents[3] / "prompts" / "summary.md"

_PROMPT_CACHE: tuple[str, str] | None = None

# per-session "摘要生成中" 标记（并发防护，设计文档 §6）
_in_progress: set[str] = set()

_TITLE_PROMPT = (
    "请为以下对话生成一个不超过 20 个字的会话标题。"
    "只输出标题本身，不要引号、不要书名号、不要结尾标点。\n\n"
    "用户: {question}\n助手: {answer}"
)

_HISTORY_MSG_MAX_CHARS = 500  # 每条历史消息注入/摘要前的截断上限（终审修订）


def _clean_history_content(content: str) -> str:
    """历史消息统一处理：注入筛查 + 截断（终审修订）。"""
    cleaned = sanitize_history(content)
    if len(cleaned) > _HISTORY_MSG_MAX_CHARS:
        cleaned = cleaned[:_HISTORY_MSG_MAX_CHARS] + "…"
    return cleaned


def _load_summary_prompt() -> tuple[str, str]:
    """Read prompts/summary.md → (system_role, user_template)。

    分节约定与 query_data._load_prompt() 一致：【系统角色】到【历史摘要】之间
    为 system，其余为 user 模板（含 {old_summary} / {new_dialogue} 占位符）。
    """
    global _PROMPT_CACHE
    if _PROMPT_CACHE is None:
        text = SUMMARY_PROMPT_PATH.read_text(encoding="utf-8")
        sys_start = text.index("【系统角色】") + len("【系统角色】")
        hist_start = text.index("【历史摘要】")
        _PROMPT_CACHE = (text[sys_start:hist_start].strip(), text[hist_start:].strip())
    return _PROMPT_CACHE


def should_summarize(total_turns: int, new_turns: int) -> bool:
    return (
        total_turns > settings.memory_summary_trigger_turns
        and new_turns > settings.memory_summary_min_new_turns
    )


def build_history_text(ctx: dict) -> str:
    """session_store.get_memory_context() 的返回 → planner 注入文本（设计文档 §6）。"""
    parts = []
    if ctx["summary"]:
        parts.append(f"[会话摘要]\n{ctx['summary']}")
    if ctx["recent"]:
        lines = [
            f"{'用户' if m['role'] == 'user' else '助手'}: {_clean_history_content(m['content'])}"
            for m in ctx["recent"]
        ]
        parts.append("[最近对话]\n" + "\n".join(lines))
    return "\n\n".join(parts)


async def maybe_summarize(session_id: str, client=None) -> bool:
    """满足触发条件时后台生成摘要。并发防护：同 session 进行中则跳过。"""
    if session_id in _in_progress:
        return False
    try:
        sess = await asyncio.to_thread(session_store.get_session, session_id)
        if sess is None:
            return False
        total = await asyncio.to_thread(session_store.count_turns, session_id)
        new = await asyncio.to_thread(
            session_store.count_new_turns, session_id, sess["summary_upto"] or 0
        )
        if not should_summarize(total, new):
            return False

        _in_progress.add(session_id)
        try:
            msgs = await asyncio.to_thread(
                session_store.list_messages_after, session_id, sess["summary_upto"] or 0
            )
            if not msgs:
                return False
            new_dialogue = "\n".join(
                f"{'用户' if m['role'] == 'user' else '助手'}: {_clean_history_content(m['content'])}"
                for m in msgs
            )
            system, template = _load_summary_prompt()
            llm = client or get_client()
            resp = await asyncio.to_thread(
                llm.chat.completions.create,
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": template.format(
                            old_summary=sess["summary"] or "(无)",
                            new_dialogue=new_dialogue,
                        ),
                    },
                ],
                temperature=settings.summarizer_temperature,
            )
            summary = (resp.choices[0].message.content or "").strip()
            if not summary:
                return False
            await asyncio.to_thread(
                session_store.update_summary, session_id, summary, msgs[-1]["id"]
            )
            return True
        finally:
            _in_progress.discard(session_id)
    except Exception:
        # 摘要失败静默，下一轮再试（设计文档 §10）
        logger.exception("Summary generation failed for session %s", session_id)
        _in_progress.discard(session_id)
        return False


async def generate_title(session_id: str, question: str, answer: str, client=None) -> bool:
    """首条 assistant 完成后异步生成标题；已有标题则跳过；失败降级为问题前 20 字。"""
    try:
        sess = await asyncio.to_thread(session_store.get_session, session_id)
        if sess is None or sess["title"]:
            return False
        llm = client or get_client()
        resp = await asyncio.to_thread(
            llm.chat.completions.create,
            model=settings.deepseek_model,
            messages=[
                {
                    "role": "user",
                    "content": _TITLE_PROMPT.format(
                        question=question[:500], answer=answer[:500]
                    ),
                }
            ],
            temperature=settings.summarizer_temperature,
        )
        title = (resp.choices[0].message.content or "").strip()[:20]
        if not title:
            title = question.strip()[:20]
        await asyncio.to_thread(session_store.rename_session, session_id, title)
        return True
    except Exception:
        logger.exception("Title generation failed for session %s", session_id)
        try:
            await asyncio.to_thread(
                session_store.rename_session, session_id, question.strip()[:20] or "新会话"
            )
        except Exception:
            logger.exception("Title fallback failed for session %s", session_id)
        return False
