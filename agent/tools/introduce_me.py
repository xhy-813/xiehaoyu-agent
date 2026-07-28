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
from configs.settings import settings
from rag.retriever import Hit, retrieve


PERSONA_PATH = Path(__file__).resolve().parents[2] / "prompts" / "system_persona.md"
RAG_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "introduce_me.md"


@dataclass
class IntroduceResult:
    answer: str
    citations: list[dict]  # [{source, heading, distance, similarity}]
    hits: list[Hit]


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
    hits = retrieve(question, top_k=top_k)
    persona = PERSONA_PATH.read_text(encoding="utf-8")
    context = _format_context(hits) or "(暂无检索片段)"

    rag_template = RAG_PROMPT_PATH.read_text(encoding="utf-8")
    user_prompt = rag_template.format(context=context, question=question)

    client = get_client()
    resp = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": persona},
            {"role": "user", "content": user_prompt},
        ],
        temperature=settings.rag_temperature,
    )
    answer = (resp.choices[0].message.content or "").strip()
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