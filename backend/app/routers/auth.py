"""POST /api/auth/login — access-code → JWT token."""

from __future__ import annotations

import secrets
import time

import jwt
from fastapi import APIRouter, HTTPException, status

from backend.app.schemas.auth import LoginRequest, TokenResponse
from configs.settings import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    """Validate access code and return a signed JWT."""
    if not secrets.compare_digest(body.access_code, settings.access_code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="访问码错误",
        )

    now = int(time.time())
    token = jwt.encode(
        {
            "sub": "user",
            "iat": now,
            "exp": now + settings.jwt_expire_hours * 3600,
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    return TokenResponse(access_token=token)