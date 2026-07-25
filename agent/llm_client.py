"""Shared OpenAI client factory for all agent modules.

Provides a single :func:`get_client` function so that every tool and the
planner use the same client configuration.  Previously this function was
copied verbatim into four separate files.
"""

from __future__ import annotations

from openai import OpenAI

from configs.settings import settings


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
    )