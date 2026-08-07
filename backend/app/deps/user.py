"""X-User-Id 匿名身份解析（设计文档 §2）。

后端不做鉴权，只做格式校验与归属校验（归属校验在各 router 内做）。
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, Request


def _parse(raw: str) -> str:
    try:
        uuid.UUID(raw)
    except ValueError:
        raise HTTPException(status_code=400, detail="X-User-Id 格式非法（需为 UUID）")
    return raw


def get_user_id(request: Request) -> str:
    """Sessions API 用：缺失 → 400，非法 → 400。"""
    raw = request.headers.get("x-user-id", "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="缺少 X-User-Id 请求头")
    return _parse(raw)


def get_user_id_optional(request: Request) -> str | None:
    """/api/chat 用：缺失 → None（匿名兼容模式，不落库）；非法 → 400。"""
    raw = request.headers.get("x-user-id", "").strip()
    if not raw:
        return None
    return _parse(raw)
