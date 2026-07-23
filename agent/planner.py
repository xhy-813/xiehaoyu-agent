"""LLM planner: emits {action, tool, args} or {action: finalize, answer}.

规划器接收用户问题 + 已执行轨迹，输出 JSON 决策：
  - 调用工具：{"action": "call", "tool": "introduce_me", "args": {"question": "..."}}
  - 结束回答：{"action": "finalize", "answer": "最终回答"}
"""

from __future__ import annotations

import json
import re

from openai import OpenAI

from configs.settings import settings


PLANNER_SYSTEM = """\
你是 Agent 规划器。根据用户问题和已有工具执行结果，决定下一步动作。

【可用工具】
1. introduce_me(question) — 检索个人知识库，回答关于本人的问题
2. query_data(question) — 自然语言查 Olist 电商数据集，返回 SQL + 结果表
3. visualize(question) — 根据最近一次 query_data 的结果自动画图（必须先执行 query_data）
4. explain_result(question) — 对最近一次 query_data 的结果做自然语言解读（必须先执行 query_data）

【输出格式】
严格输出 JSON，不要输出任何其他内容。

调用工具：
{"action": "call", "tool": "工具名", "args": {"question": "参数值"}}

结束回答：
{"action": "finalize", "answer": "最终回答文本"}

【规则】
- 每次只调用一个工具
- visualize 和 explain_result 依赖 query_data 的结果，必须先执行 query_data
- 当已有足够信息回答用户问题时，选择 finalize
- 不要虚构信息，不确定时调用 introduce_me 检索
- 如果用户要求画图或解读，确保按顺序调用 query_data → visualize/explain_result → finalize
- finalize 的 answer 应该是综合所有工具结果的完整回答，用中文
"""


def _client() -> OpenAI:
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set in .env")
    return OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )


def _extract_json(raw: str) -> dict:
    """Parse JSON from LLM output, handling markdown code blocks."""
    raw = raw.strip()
    # Strip markdown code block wrapper
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [l for l in lines[1:] if not l.strip() == "```"]
        raw = "\n".join(lines).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: extract first {...} block
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Planner output is not valid JSON: {raw}")


def plan(question: str, trace: list[dict], client: OpenAI | None = None) -> dict:
    """Call LLM to decide next action.

    Returns:
        {"action": "call", "tool": str, "args": dict}
        {"action": "finalize", "answer": str}
    """
    client = client or _client()

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
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.0,
    )
    raw = resp.choices[0].message.content or ""
    return _extract_json(raw)
