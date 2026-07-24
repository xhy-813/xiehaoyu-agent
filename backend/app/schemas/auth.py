"""Pydantic models for auth endpoints."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    access_code: str = Field(..., min_length=1, description="访问码")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"