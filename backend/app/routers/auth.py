"""POST /api/auth/login — access-code → JWT token."""

from __future__ import annotations

import secrets
import time

import jwt
from fastapi import APIRouter, HTTPException, Request, status

from backend.app.deps.rate_limit import check_login_rate_limit
from backend.app.schemas.auth import LoginRequest, TokenResponse
from configs.settings import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request) -> TokenResponse:
    """Validate access code and return a signed JWT."""
    check_login_rate_limit(client_ip=request.client.host if request.client else "unknown")

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