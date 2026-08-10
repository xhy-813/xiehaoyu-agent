"""introduce_me tool: RAG over the personal knowledge base.

流程：
1. retriever.retrieve(question, top_k)
2. 构造 prompt：system_persona + 检索片段 + 用户问题
3. 调 DeepSeek 生成回答
4. 返回回答 + 引用来源列表
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path

from openai import AsyncOpenAI

from agent.llm_client import alogged_chat_create, get_async_client
from agent.sanitize import sanitize_input
from configs.settings import settings
from rag.retriever import Hit, RetrievalResult, retrieve_result


PERSONA_PATH = Path(__file__).resolve().parents[2] / "prompts" / "system_persona.md"
RAG_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "introduce_me.md"


@dataclass
class IntroduceResult:
    answer: str
    citations: list[dict]  # [{source, heading, distance, similarity}]
    hits: list[Hit]
    degraded: bool = False  # 检索基础设施故障（808 审查 M9）


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


async def introduce_me_async(
    question: str, top_k: int = 10, client: AsyncOpenAI | None = None
) -> IntroduceResult:
    """RAG-based self-introduction（异步版，808 审查 M1）。

    Retrieves top_k relevant chunks from the personal knowledge base,
    then asks the LLM to synthesize a natural, first-person answer.
    检索（Chroma + embedding API）为同步阻塞调用，经 to_thread 隔离；
    LLM 调用为真异步——任务取消时 HTTP 请求即中止。
    """
    safe_question = sanitize_input(question)
    retrieval: RetrievalResult = await asyncio.to_thread(
        retrieve_result, safe_question, top_k
    )
    hits = retrieval.hits
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

    # 808 审查 M9：检索基础设施故障时明确指示诚实说明，防止凭人设编造经历
    if retrieval.degraded:
        user_prompt += (
            "\n\n【重要】知识库检索当前不可用（基础设施故障，非无匹配）。"
            "请诚实说明知识库暂时无法访问，建议对方稍后再试；"
            "不要凭印象编造任何经历、数据或细节。"
        )

    owns_client = client is None
    client = client or get_async_client()
    try:
        try:
            resp = await alogged_chat_create(
                client,
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": persona},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=settings.rag_temperature,
                caller="introduce_me",
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
        return IntroduceResult(
            answer=answer, citations=citations, hits=hits, degraded=retrieval.degraded
        )
    finally:
        if owns_client:
            await client.close()  # 自建客户端随用随关


def introduce_me(question: str, top_k: int = 10) -> IntroduceResult:
    """同步门面（smoke 脚本/离线测试用）。异步链路请直接 await introduce_me_async。"""
    return asyncio.run(introduce_me_async(question, top_k))