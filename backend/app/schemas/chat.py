"""Pydantic models for chat endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=10000, description="用户问题")
    session_id: Optional[str] = Field(
        None,
        description="会话 ID（可选；带 X-User-Id 且为空时自动新建）",
    )
