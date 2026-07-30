"""LLM planner: emits {action, tool, args} or {action: finalize, answer}.

规划器接收用户问题 + 已执行轨迹，输出 JSON 决策：
  - 调用工具：{"action": "call", "tool": "introduce_me", "args": {"question": "..."}}
  - 结束回答：{"action": "finalize", "answer": "最终回答"}
"""

from __future__ import annotations

import json
from pathlib import Path

from openai import OpenAI

from agent.llm_client import get_client
from configs.settings import settings


PLANNER_PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "planner.md"

# Module-level prompt cache — loaded once from disk
_PLANNER_SYSTEM: str | None = None


def _load_planner_system() -> str:
    global _PLANNER_SYSTEM
    if _PLANNER_SYSTEM is None:
        _PLANNER_SYSTEM = PLANNER_PROMPT_PATH.read_text(encoding="utf-8")
    return _PLANNER_SYSTEM


def _extract_json(raw: str) -> dict:
    """Parse JSON from LLM output, handling markdown code blocks and
    nested braces (e.g. ``{"answer": "使用 Pandas (Python 库)"}``).

    Uses brace counting to find the outermost JSON object rather than
    a non-greedy regex, which would truncate on the first ``}``.
    """
    raw = raw.strip()
    # Strip markdown code block wrapper
    if raw.startswith("```"):
        lines = raw.split("\n")
        lines = [l for l in lines[1:] if not l.strip() == "```"]
        raw = "\n".join(lines).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: find the outermost {...} using brace counting
        start = raw.find("{")
        if start == -1:
            raise ValueError(f"Planner output is not valid JSON: {raw}")
        depth = 0
        for i in range(start, len(raw)):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(raw[start : i + 1])
        raise ValueError(f"Planner JSON has unmatched braces: {raw}")


def plan(question: str, trace: list[dict], client: OpenAI | None = None) -> dict:
    """Call LLM to decide next action.

    Returns:
        {"action": "call", "tool": str, "args": dict}
        {"action": "finalize", "answer": str}
    """
    client = client or get_client()

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

    resp = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": _load_planner_system()},
            {"role": "user", "content": user_msg},
        ],
        temperature=settings.planner_temperature,
    )
    raw = resp.choices[0].message.content or ""
    return _extract_json(raw)
