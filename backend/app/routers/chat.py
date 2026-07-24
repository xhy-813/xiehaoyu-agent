"""POST /api/chat — SSE streaming endpoint.

Reads the user question, runs the LangGraph agent via ``stream_run()``,
and pushes each execution step to the client as an SSE event.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.app.dependencies import get_current_user
from backend.app.middleware.rate_limit import check_rate_limit
from backend.app.schemas.chat import ChatRequest

# Ensure the project root is on sys.path so agent / configs / chatbi / rag
# can be imported from the backend sub-package.
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.graph import stream_run  # noqa: E402  (import after path setup)

router = APIRouter(prefix="/api/chat", tags=["chat"])


async def _event_generator(question: str) -> str:
    """Yield SSE-formatted lines for each agent step."""
    try:
        async for event in stream_run(question):
            line = json.dumps(event, ensure_ascii=False)
            yield f"data: {line}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as exc:
        err = json.dumps({"type": "error", "data": {"message": str(exc)}}, ensure_ascii=False)
        yield f"data: {err}\n\n"


@router.post("")
async def chat(
    body: ChatRequest,
    _user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """Send a question and receive agent execution steps as SSE events.

    Requires a valid JWT in the ``Authorization`` header.  Each SSE event
    is a JSON object with ``type``, ``node``, and ``data`` fields.
    The stream ends with ``data: [DONE]``.
    """
    check_rate_limit()

    return StreamingResponse(
        _event_generator(body.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable Nginx buffering
        },
    )