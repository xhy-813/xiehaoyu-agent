"""Pydantic models for session endpoints."""

from pydantic import BaseModel, Field


class RenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="会话标题")