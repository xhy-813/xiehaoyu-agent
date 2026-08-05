"""Input sanitization shared across agent modules.

Provides a single ``sanitize_input()`` function used by planner, introduce_me,
and other tools to detect and strip prompt-injection attempts before the user
input reaches any LLM call.
"""

from __future__ import annotations

import re

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
            raise ValueError(
                f"Input contains potentially unsafe content: {pattern.pattern}"
            )

    return cleaned