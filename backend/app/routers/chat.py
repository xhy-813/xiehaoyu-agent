"""POST /api/chat — SSE streaming endpoint.

Reads the user question, runs the LangGraph agent via ``stream_run()``,
and pushes each execution step to the client as an SSE event.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from backend.app.dependencies import get_current_user
from backend.app.deps.rate_limit import check_rate_limit
from backend.app.schemas.chat import ChatRequest

from agent.graph import stream_run

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])


async def _event_generator(question: str, request: Request) -> str:
    """Yield SSE-formatted lines for each agent step, checking for
    client disconnect on each iteration.  Sends a heartbeat comment
    every 15 seconds to keep the connection alive."""
    import asyncio
    heartbeat_interval = 15  # seconds

    async def _heartbeat():
        while True:
            await asyncio.sleep(heartbeat_interval)
            yield ": heartbeat\n\n"

    try:
        async for event in stream_run(question):
            if await request.is_disconnected():
                break
            line = json.dumps(event, ensure_ascii=False)
            yield f"data: {line}\n\n"
        yield "data: [DONE]\n\n"
    except Exception:
        logger.exception("SSE stream failed for question: %s", question[:200])
        err = json.dumps(
            {"type": "error", "data": {"message": "服务器内部错误，请稍后重试"}},
            ensure_ascii=False,
        )
        yield f"data: {err}\n\n"


@router.post("")
async def chat(
    body: ChatRequest,
    request: Request,
    _user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """Send a question and receive agent execution steps as SSE events.

    Requires a valid JWT in the ``Authorization`` header.  Each SSE event
    is a JSON object with ``type``, ``node``, and ``data`` fields.
    The stream ends with ``data: [DONE]``.
    """
    check_rate_limit(user_id=_user.get("sub", "default"))

    return StreamingResponse(
        _event_generator(body.question, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable Nginx buffering
        },
    )