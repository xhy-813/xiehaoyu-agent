"""Pydantic models for chat endpoints."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=10000, description="用户问题")