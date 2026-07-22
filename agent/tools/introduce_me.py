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

from configs.settings import settings
from rag.retriever import Hit, retrieve


PERSONA_PATH = Path(__file__).resolve().parents[2] / "prompts" / "system_persona.md"


@dataclass
class IntroduceResult:
    answer: str
    citations: list[dict]  # [{source, heading, score}]
    hits: list[Hit]


def _client() -> OpenAI:
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set in .env")
    return OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )


def _format_context(hits: list[Hit]) -> str:
    parts = []
    for i, h in enumerate(hits, 1):
        header = f"[{i}] source={h.source}"
        if h.heading:
            header += f"  heading={h.heading}"
        parts.append(f"{header}\n{h.content}")
    return "\n\n---\n\n".join(parts)


def introduce_me(question: str, top_k: int = 5) -> IntroduceResult:
    hits = retrieve(question, top_k=top_k)
    persona = PERSONA_PATH.read_text(encoding="utf-8")
    context = _format_context(hits) or "(暂无检索片段)"

    user_prompt = (
        "以下是从我的个人知识库检索到的相关片段，请**仅基于这些片段**回答用户问题。"
        "若信息不足，请如实说明；不要虚构。回答末尾用 [编号] 标注引用。\n\n"
        f"【检索片段】\n{context}\n\n"
        f"【用户问题】\n{question}"
    )

    client = _client()
    resp = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": persona},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    answer = (resp.choices[0].message.content or "").strip()
    citations = [
        {"source": h.source, "heading": h.heading, "score": round(h.score, 4)} for h in hits
    ]
    return IntroduceResult(answer=answer, citations=citations, hits=hits)
