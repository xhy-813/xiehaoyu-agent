"""FastAPI dependency: verify JWT Bearer token."""

from __future__ import annotations

import jwt
from fastapi import Depends, HTTPException, Header, status

from configs.settings import settings


def get_current_user(authorization: str = Header(...)) -> dict:
    """Decode and validate the JWT from the Authorization header.

    Returns the decoded payload dict on success; raises 401 otherwise.
    """
    try:
        scheme, token = authorization.split(" ", 1)
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization scheme must be 'Bearer'",
            )
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token 已过期，请重新登录"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="未授权访问"
        )