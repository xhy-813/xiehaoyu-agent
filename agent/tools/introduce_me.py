"""introduce_me tool: RAG over the personal knowledge base.

流程：
1. retriever.retrieve(question, top_k)
2. 构造 prompt：system_persona + 检索片段 + 用户问题
3. 调 DeepSeek 生成回答
4. 返回回答 + 引用来源列表
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from agent.llm_client import get_client
from configs.settings import settings
from rag.retriever import Hit, retrieve


PERSONA_PATH = Path(__file__).resolve().parents[2] / "prompts" / "system_persona.md"
RAG_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "introduce_me.md"


@dataclass
class IntroduceResult:
    answer: str
    citations: list[dict]  # [{source, heading, distance, similarity}]
    hits: list[Hit]


# Patterns that indicate prompt-injection attempts
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above|the\s+above)\s+(instructions?|rules?|constraints?)", re.IGNORECASE),
    re.compile(r"(system|assistant|user):\s*$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"you\s+are\s+now\s+(a\s+)?(different|new|another)\s+(assistant|ai|bot|agent)", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all)\s+(you\s+know|you.ve\s+(learned|been\s+told))", re.IGNORECASE),
    re.compile(r"\[system\]\s*\(", re.IGNORECASE),
    re.compile(r"<\|im_start\|>|<\|im_end\|>", re.IGNORECASE),
    re.compile(r"```\s*(system|assistant|user)\s*$", re.IGNORECASE | re.MULTILINE),
]


def _sanitize_input(text: str) -> str:
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
            raise ValueError(f"Input contains potentially unsafe content: {pattern.pattern}")

    return cleaned


def _format_context(hits: list[Hit]) -> str:
    parts = []
    for i, h in enumerate(hits, 1):
        header = f"[片段 {i}] 来源={h.source}"
        if h.heading:
            header += f"  标题={h.heading}"
        parts.append(f"{header}\n{h.content}")
    return "\n\n---\n\n".join(parts)


def introduce_me(question: str, top_k: int = 10) -> IntroduceResult:
    """RAG-based self-introduction.

    Retrieves top_k relevant chunks from the personal knowledge base,
    then asks the LLM to synthesize a natural, first-person answer.
    """
    safe_question = _sanitize_input(question)
    hits = retrieve(safe_question, top_k=top_k)
    persona = PERSONA_PATH.read_text(encoding="utf-8")
    context = _format_context(hits) or "(暂无检索片段)"

    rag_template = RAG_PROMPT_PATH.read_text(encoding="utf-8")
    user_prompt = rag_template.format(context=context, question=safe_question)

    client = get_client()
    try:
        resp = client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": persona},
                {"role": "user", "content": user_prompt},
            ],
            temperature=settings.rag_temperature,
        )
        answer = (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        raise RuntimeError(f"introduce_me LLM call failed: {exc}") from exc
    citations = [
        {
            "source": h.source,
            "heading": h.heading,
            "distance": round(h.distance, 4),
            "similarity": h.similarity,
        }
        for h in hits
    ]
    return IntroduceResult(answer=answer, citations=citations, hits=hits)