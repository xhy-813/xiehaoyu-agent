"""introduce_me tool: RAG over the personal knowledge base.

流程：
1. retriever.retrieve(question, top_k)
2. 构造 prompt：system_persona + 检索片段 + 用户问题
3. 调 DeepSeek 生成回答
4. 返回回答 + 引用来源列表
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from openai import OpenAI

from agent.llm_client import get_client
from agent.sanitize import sanitize_input
from configs.settings import settings
from rag.retriever import Hit, retrieve


PERSONA_PATH = Path(__file__).resolve().parents[2] / "prompts" / "system_persona.md"
RAG_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "introduce_me.md"


@dataclass
class IntroduceResult:
    answer: str
    citations: list[dict]  # [{source, heading, distance, similarity}]
    hits: list[Hit]


# Self-introduction keywords used to decide whether to inject the
# structured self-intro template (saves ~200 tokens on non-intro queries).
_SELF_INTRO_KEYWORDS = [
    "介绍你自己", "介绍一下", "你是谁", "你是做什么", "你的背景",
    "自我介绍一下", "做个自我介绍", "简单介绍", "认识一下",
]


def _is_self_intro(question: str) -> bool:
    """Check if the question is a self-introduction request."""
    return any(kw in question for kw in _SELF_INTRO_KEYWORDS)


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
    safe_question = sanitize_input(question)
    hits = retrieve(safe_question, top_k=top_k)
    persona = PERSONA_PATH.read_text(encoding="utf-8")
    context = _format_context(hits) or "(暂无检索片段)"

    rag_template = RAG_PROMPT_PATH.read_text(encoding="utf-8")

    # Conditionally inject the structured self-intro template to save tokens
    # on non-intro queries (e.g. "你 K12 项目用了什么技术栈")
    if _is_self_intro(safe_question):
        user_prompt = rag_template.format(context=context, question=safe_question)
    else:
        # Remove the self-intro template section for focused queries
        no_template = rag_template.split("【自我介绍模板】")[0].strip()
        user_prompt = no_template.format(context=context, question=safe_question)

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