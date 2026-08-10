"""Input sanitization shared across agent modules.

Provides a single ``sanitize_input()`` function used by planner, introduce_me,
and other tools to detect and strip prompt-injection attempts before the user
input reaches any LLM call.
"""

from __future__ import annotations

import re


class InjectionDetected(ValueError):
    """用户输入命中注入模式。消息体刻意不包含命中的正则细节
    （808 审查 M3：此前把 pattern 原文带回给用户，等于公开检测规则）。"""

# Patterns that indicate prompt-injection attempts
_INJECTION_PATTERNS = [
    re.compile(
        r"ignore\s+(all\s+)?(previous|prior|above|the\s+above)\s+(instructions?|rules?|constraints?)",
        re.IGNORECASE,
    ),
    re.compile(r"(system|assistant|user):\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(
        r"you\s+are\s+now\s+(a\s+)?(different|new|another)\s+(assistant|ai|bot|agent)",
        re.IGNORECASE,
    ),
    re.compile(
        r"forget\s+(everything|all)\s+(you\s+know|you.ve\s+(learned|been\s+told))",
        re.IGNORECASE,
    ),
    re.compile(r"\[system\]\s*\(", re.IGNORECASE),
    re.compile(r"<\|im_start\|>|<\|im_end\|>", re.IGNORECASE),
    re.compile(r"```\s*(system|assistant|user)\s*$", re.IGNORECASE | re.MULTILINE),
    # Additional patterns for planner-level injection
    re.compile(
        r"(output|return|respond\s+with)\s+(json|only\s+json)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(skip|bypass|override)\s+(the\s+)?(planner|tool|agent)",
        re.IGNORECASE,
    ),
    # 中文注入措辞（808 审查 M2：本产品用户/攻击者主要说中文，
    # 英文模式对中文注入零覆盖）。关键词必须在场、间隔设上限，降低误杀。
    re.compile(r"忽略.{0,6}(指令|指示|规则|要求|约束|提示|设定)"),
    re.compile(r"你现在.{0,4}(是|变成|成为).{0,8}(AI|助手|机器人|智能体|模型)"),
    re.compile(r"忘记\s*(你|你的)\s*(人设|身份|角色|定位)"),
    re.compile(r"忘记\s*(所有|一切)\s*(你)?\s*(学到|知道|被告知|学过)"),
    re.compile(r"(系统|管理员)\s*[:：]\s*$", re.MULTILINE),
]


def sanitize_input(text: str) -> str:
    """Strip markdown code fences and detect obvious injection patterns.

    Returns the sanitized text, or raises ValueError if a clear injection
    attempt is detected.
    """
    # Strip markdown code fences that could be used to escape the prompt
    cleaned = re.sub(r"```[\s\S]*?```", "[code block removed]", text)
    # Strip any remaining unclosed triple-backtick markers
    cleaned = re.sub(r"```", "[code block removed]", cleaned)
    cleaned = re.sub(r"`{1,2}[^`]*`{1,2}", "[inline code removed]", cleaned)

    for pattern in _INJECTION_PATTERNS:
        if pattern.search(cleaned):
            raise InjectionDetected("Input contains potentially unsafe content")

    return cleaned


def sanitize_history(text: str) -> str:
    """历史消息注入前的轻量筛查（设计文档 §6，2026-08-07 终审决策）。

    与 sanitize_input 的区别：不剥代码块（assistant 历史可能含 SQL 代码块）、
    不抛异常——命中注入模式时整条替换为占位符。仅用于服务端拼装的历史上下文，
    落库内容仍是原文（回放保真不受影响）。
    """
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return "[历史内容已过滤]"
    return text
