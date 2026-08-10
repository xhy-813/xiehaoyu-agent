"""LLM planner: emits {action, tool, args} or {action: finalize, answer}.

规划器接收用户问题 + 已执行轨迹，输出 JSON 决策：
  - 调用工具：{"action": "call", "tool": "introduce_me", "args": {"question": "..."}}
  - 结束回答：{"action": "finalize", "answer": "最终回答"}
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from openai import AsyncOpenAI

from agent.llm_client import alogged_chat_create, get_async_client
from agent.sanitize import sanitize_input
from configs.settings import settings

logger = logging.getLogger(__name__)

PLANNER_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "planner.md"

# Module-level prompt cache — loaded once from disk
_PLANNER_SYSTEM: str | None = None


def _load_planner_system() -> str:
    global _PLANNER_SYSTEM
    if _PLANNER_SYSTEM is None:
        _PLANNER_SYSTEM = PLANNER_PROMPT_PATH.read_text(encoding="utf-8")
    return _PLANNER_SYSTEM


def _sanitize_control_chars(s: str) -> str:
    """Escape bare control characters inside JSON string values.

    LLMs occasionally emit literal newlines inside JSON string values, which
    violates the JSON spec and causes JSONDecodeError.  Only characters
    *inside* ``"..."`` are escaped — structural whitespace between tokens
    (``\\n``/``\\r``/``\\t``) is valid JSON and must be left untouched,
    otherwise pretty-printed multi-line JSON becomes unparseable
    (808 审查 H1 回归修复：早期版本无差别转义全部控制字符）。
    """
    _ESCAPE_MAP = {"\n": "\\n", "\r": "\\r", "\t": "\\t"}

    out: list[str] = []
    in_string = False
    escaped = False
    for ch in s:
        if in_string:
            if escaped:
                out.append(ch)
                escaped = False
            elif ch == "\\":
                out.append(ch)
                escaped = True
            elif ch == '"':
                out.append(ch)
                in_string = False
            elif ch < "\x20":
                out.append(_ESCAPE_MAP.get(ch, f"\\u{ord(ch):04x}"))
            else:
                out.append(ch)
        else:
            if ch == '"':
                in_string = True
                out.append(ch)
            elif ch < "\x20" and ch not in ("\n", "\r", "\t"):
                # Stray control char outside strings: not valid JSON whitespace
                out.append(" ")
            else:
                out.append(ch)
    return "".join(out)


def _extract_json(raw: str) -> dict:
    """Parse JSON from LLM output, handling markdown code blocks and
    nested braces (e.g. ``{"answer": "使用 Pandas (Python 库)"}``).

    Uses brace counting to find the outermost JSON object rather than
    a non-greedy regex, which would truncate on the first ``}``.
    """
    raw = raw.strip()
    if not raw:
        raise ValueError("LLM returned empty response")

    # Strip markdown code block wrapper
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines[1:] if not l.strip() == "```"]
        raw = "\n".join(lines).strip()

    # Escape bare control characters that LLMs occasionally emit inside strings
    raw = _sanitize_control_chars(raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: find the outermost {...} using brace counting that is
        # aware of string literals (braces inside "..." are not structural).
        start = raw.find("{")
        if start == -1:
            raise ValueError(f"Planner output is not valid JSON: {raw[:200]}")
        depth = 0
        in_string = False
        escaped = False
        for i in range(start, len(raw)):
            ch = raw[i]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(raw[start : i + 1])
        raise ValueError(f"Planner JSON has unmatched braces: {raw[:200]}")


async def plan(
    question: str,
    trace: list[dict],
    client: AsyncOpenAI | None = None,
    history_text: str = "",
) -> dict:
    """Call LLM to decide next action.

    异步实现（808 审查 M1）：await 点即取消点——SSE 断连取消任务时，
    进行中的 HTTP 请求被真正中止，不再继续计费。

    When ``history_text`` is non-empty it is injected as a separate
    user message between the system prompt and the current question,
    so the planner can resolve anaphora ("那 2017 年呢") without the
    tools seeing the conversation history.

    Returns:
        {"action": "call", "tool": str, "args": dict}
        {"action": "finalize", "answer": str}
    """
    owns_client = client is None
    client = client or get_async_client()

    try:
        # Sanitize user input to prevent prompt injection
        question = sanitize_input(question)

        # Build trace context
        if trace:
            parts = []
            for i, t in enumerate(trace, 1):
                parts.append(f"步骤 {i}: {t['tool']}({t['args']})\n结果: {t['summary']}")
            trace_text = "\n\n".join(parts)
        else:
            trace_text = "(尚未执行任何工具)"

        user_msg = (
            f"【用户问题】\n{question}\n\n"
            f"【已执行步骤】\n{trace_text}\n\n"
            f"请决定下一步动作。"
        )

        messages = [
            {"role": "system", "content": _load_planner_system()},
        ]
        if history_text:
            # 会话记忆（摘要 + 最近 N 轮）作为独立 user 消息注入（设计文档 §6）；
            # history_text 由服务端拼装，不过 sanitize
            messages.append({"role": "user", "content": history_text})
        messages.append({"role": "user", "content": user_msg})

        resp = await alogged_chat_create(
            client,
            model=settings.deepseek_model,
            messages=messages,
            temperature=settings.planner_temperature,
            caller="planner",
        )
        raw = resp.choices[0].message.content or ""

        # Guard against empty LLM response (e.g. API filter, model refusal)
        if not raw.strip():
            logger.warning(
                "Planner LLM returned empty response. "
                "finish_reason=%s",
                resp.choices[0].finish_reason,
            )
            # Fallback: route based on question intent so a transient empty
            # response doesn't silently discard a valid request.
            if not trace:
                intro_keywords = ["介绍", "你是谁", "你叫什么", "认识你", "你的背景"]
                if any(kw in question for kw in intro_keywords):
                    return {
                        "action": "call",
                        "tool": "introduce_me",
                        "args": {"question": question},
                    }
                data_keywords = [
                    "查", "统计", "排名", "Top", "top", "最高", "最低",
                    "趋势", "对比", "订单", "销售", "金额", "数据", "分析",
                    "多少", "平均", "占比", "画图", "可视化", "图表",
                ]
                if any(kw in question for kw in data_keywords):
                    return {
                        "action": "call",
                        "tool": "query_data",
                        "args": {"question": question},
                    }
            return {
                "action": "finalize",
                "answer": "抱歉，我暂时无法处理这个请求，请稍后再试。",
            }

        return _extract_json(raw)
    finally:
        if owns_client:
            await client.close()  # 自建客户端随用随关（短生命周期事件循环下不留连接噪音）
