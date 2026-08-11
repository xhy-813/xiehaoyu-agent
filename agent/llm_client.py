"""Shared OpenAI client factory for all agent modules.

Provides a single :func:`get_client` function so that every tool and the
planner use the same client configuration.  Previously this function was
copied verbatim into four separate files.

808 审查 M1：新增异步客户端与异步调用封装——``AsyncOpenAI`` 协程在
asyncio 任务被取消时会真正中止进行中的 HTTP 请求（同步线程调用无法被
中断，断连后仍会继续计费）。
"""

from __future__ import annotations

import logging

import httpx
from openai import AsyncOpenAI, OpenAI

from configs.settings import settings

logger = logging.getLogger(__name__)

# trust_env=False：不读系统/环境代理。DeepSeek、智谱均为国内 API，走代理只
# 引入单点故障（2026-08-10 本地故障：Windows 系统代理残留导致 TLS 建连失败
# ConnectError，后台标题生成报错）。若未来 base_url 切到海外 API 需改回。


def get_client() -> OpenAI:
    """Return a configured OpenAI client pointed at DeepSeek.

    Raises:
        RuntimeError: if ``DEEPSEEK_API_KEY`` is not set.
    """
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set in .env")
    return OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        timeout=30.0,
        max_retries=1,
        http_client=httpx.Client(trust_env=False, timeout=30.0),
    )


def get_async_client() -> AsyncOpenAI:
    """异步客户端（SSE 流式链路专用）：取消协程即中止 HTTP 请求（M1）。"""
    if not settings.deepseek_api_key:
        raise RuntimeError("DEEPSEEK_API_KEY not set in .env")
    return AsyncOpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        timeout=30.0,
        max_retries=1,
        http_client=httpx.AsyncClient(trust_env=False, timeout=30.0),
    )


def _log_usage(usage, model: str, caller: str) -> None:
    """记录单次调用的 token 消耗（808 审查 M10）。

    DeepSeek 按 token 计费。所有调用点经封装后，额度异常（限流绕过、
    重试风暴）可以从日志趋势中发现，而不是等月底账单。
    """
    if usage is not None:
        logger.info(
            "llm_tokens caller=%s model=%s prompt=%s completion=%s total=%s",
            caller or "?",
            model,
            getattr(usage, "prompt_tokens", "?"),
            getattr(usage, "completion_tokens", "?"),
            getattr(usage, "total_tokens", "?"),
        )


def logged_chat_create(client: OpenAI, *, caller: str = "", **kwargs):
    """同步 ``chat.completions.create`` 封装：记录 token 消耗（M10）。"""
    resp = client.chat.completions.create(**kwargs)
    _log_usage(getattr(resp, "usage", None), kwargs.get("model", "?"), caller)
    return resp


async def alogged_chat_create(client: AsyncOpenAI, *, caller: str = "", **kwargs):
    """异步 ``chat.completions.create`` 封装：记录 token 消耗（M10/M1）。

    await 点即取消点：asyncio 任务被取消时，进行中的 HTTP 请求随之终止。
    """
    resp = await client.chat.completions.create(**kwargs)
    _log_usage(getattr(resp, "usage", None), kwargs.get("model", "?"), caller)
    return resp
