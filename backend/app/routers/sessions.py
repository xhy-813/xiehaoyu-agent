"""会话 CRUD + 回放 API（设计文档 §5）。

路由注册顺序注意：``/search`` 必须在 ``/{session_id}`` 之前，
否则 "search" 会被当作 session_id 匹配。
"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Request

from backend.app.deps.user import get_user_id
from backend.app.schemas.session import RenameRequest
from backend.app.services import session_store

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _load_owned_session(session_id: str, user_id: str) -> dict:
    """归属校验：不存在 → 404，非本人 → 403（设计文档 §2）。"""
    sess = session_store.get_session(session_id)
    if sess is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    if sess["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="无权访问该会话")
    return sess


@router.post("")
async def create_session(request: Request) -> dict:
    user_id = get_user_id(request)
    sid = await asyncio.to_thread(session_store.create_session, user_id)
    return {"session_id": sid}


@router.get("")
async def list_sessions(request: Request) -> dict:
    user_id = get_user_id(request)
    sessions = await asyncio.to_thread(session_store.list_sessions, user_id)
    return {"sessions": sessions}


@router.get("/search")
async def search_sessions(request: Request, q: str = "") -> dict:
    user_id = get_user_id(request)
    results = await asyncio.to_thread(session_store.search_sessions, user_id, q)
    return {"sessions": results}


@router.get("/{session_id}")
async def replay_session(session_id: str, request: Request) -> dict:
    """回放协议（设计文档 §5）：trace 原样返回，steps/tools 由 trace 推导。"""
    user_id = get_user_id(request)
    sess = await asyncio.to_thread(_load_owned_session, session_id, user_id)
    rows = await asyncio.to_thread(session_store.list_messages, session_id)
    messages = []
    for m in rows:
        trace = json.loads(m["artifacts_json"]) if m["artifacts_json"] else None
        messages.append(
            {
                "id": m["id"],
                "role": m["role"],
                "content": m["content"],
                "steps": len(trace) if trace else None,
                "tools": list(dict.fromkeys(t["tool"] for t in trace)) if trace else None,
                "trace": trace,
                "created_at": m["created_at"],
            }
        )
    return {
        "session": {
            "id": sess["id"],
            "title": sess["title"],
            "created_at": sess["created_at"],
            "updated_at": sess["updated_at"],
        },
        "messages": messages,
    }


@router.patch("/{session_id}")
async def rename_session(session_id: str, body: RenameRequest, request: Request) -> dict:
    user_id = get_user_id(request)
    await asyncio.to_thread(_load_owned_session, session_id, user_id)
    await asyncio.to_thread(session_store.rename_session, session_id, body.title)
    return {"ok": True}


@router.delete("/{session_id}")
async def delete_session(session_id: str, request: Request) -> dict:
    user_id = get_user_id(request)
    await asyncio.to_thread(_load_owned_session, session_id, user_id)
    await asyncio.to_thread(session_store.delete_session, session_id)
    return {"ok": True}
