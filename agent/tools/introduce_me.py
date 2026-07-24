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

    user_prompt = (
        "以下是从我的个人知识库检索到的相关片段。请根据这些片段，用第一人称回答用户的问题。\n\n"
        "【重要规则】\n"
        "1. 你是谢浩宇本人，用「我」来回答，自然、真诚、有细节\n"
        "2. 综合多个片段的信息，组织成连贯的回答，不要逐条复述\n"
        "3. 优先使用数字和具体案例，不要泛泛而谈\n"
        "4. 如果片段信息不足，诚实说明，不要编造\n"
        "5. 回答末尾用 [来源: 文件名] 标注引用的片段\n\n"
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