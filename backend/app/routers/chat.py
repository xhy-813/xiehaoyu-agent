"""POST /api/chat — SSE streaming endpoint with session persistence.

Reads the user question, runs the LangGraph agent via ``stream_run()``,
and pushes each execution step to the client as an SSE event.

会话持久化（设计文档 §5/§10）：
- 带 X-User-Id 的请求：校验/创建会话，planner 前注入记忆（摘要+最近 N 轮），
  流结束（含用户停止/断连）后落库本轮消息，并异步触发摘要与标题生成
- 不带 X-User-Id：匿名兼容模式，行为与持久化之前完全一致
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.app.deps.rate_limit import (
    check_global_daily_cap,
    check_rate_limit,
    get_client_ip,
)
from backend.app.deps.user import get_user_id_optional
from backend.app.schemas.chat import ChatRequest
from backend.app.services import session_store, summarizer
from configs.settings import settings

from agent.graph import stream_run

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

HEARTBEAT_INTERVAL = 15  # seconds

# fire-and-forget 后台任务登记（事件循环对 task 只持弱引用，不登记可能被 GC
# 提前回收——终审修订；用于摘要/标题/兜底落库）
_background_tasks: set[asyncio.Task] = set()


def _spawn(coro) -> None:
    """创建后台任务并保持强引用直到完成。"""
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


def _trace_to_json(trace_events: list[dict]) -> str | None:
    """Collected tool_end payloads → 可落库的 trace JSON（保持 df_json 等字符串不解析）。"""
    trace = [
        {
            "tool": e.get("tool", ""),
            "args": e.get("args", {}),
            "summary": e.get("summary", ""),
            "artifact": e.get("artifact"),
        }
        for e in trace_events
    ]
    if not trace:
        return None
    return json.dumps(trace, ensure_ascii=False)


async def _persist_turn(
    session_id: str, question: str, answer: str, trace_events: list[dict]
) -> None:
    """Best-effort 落库：失败记 log，绝不影响 SSE 流（设计文档 §10）。"""
    try:
        await asyncio.to_thread(
            session_store.append_message, session_id, "user", question, None
        )
        await asyncio.to_thread(
            session_store.append_message,
            session_id,
            "assistant",
            answer,
            _trace_to_json(trace_events),
        )
    except Exception:
        logger.exception("Failed to persist turn for session %s", session_id)


async def _event_generator(
    question: str,
    request: Request,
    *,
    user_id: str | None,
    session_id: str | None,
    history_text: str,
):
    """Yield SSE lines per agent step.

    心跳：15s 无事件则发 ``: heartbeat`` 注释行（修复原 _heartbeat 死代码）。
    断连：检测后立即停止，不再发 [DONE]（修复原 break 后仍 yield [DONE]）。
    落库：正常/异常路径在流内 await 完成；客户端强断开（GeneratorExit）
    路径在 finally 里 fire-and-forget，三条路径由 persisted 标记保证只跑一次。
    """
    req_id = uuid.uuid4().hex[:8]  # 808 审查 M14：请求级关联 ID，贯穿本条流的日志
    logger.info(
        "chat start req=%s user=%s session=%s",
        req_id, (user_id or "anon")[:8], (session_id or "-")[:8],
    )
    queue: asyncio.Queue = asyncio.Queue()

    async def _produce():
        try:
            async for event in stream_run(question, history_text=history_text):
                await queue.put(("event", event))
            await queue.put(("done", None))
        except Exception as exc:  # noqa: BLE001 — 统一转成 error 事件
            await queue.put(("error", exc))

    producer = asyncio.create_task(_produce())
    trace_events: list[dict] = []
    final_answer = ""
    disconnected = False
    persisted = False

    async def _finalize() -> None:
        """落库本轮 + 触发摘要/标题。幂等（persisted 标记）。"""
        nonlocal persisted
        if persisted or not (user_id and session_id):
            return
        persisted = True
        await _persist_turn(
            session_id, question, final_answer or "（本轮回答未完成）", trace_events
        )
        _spawn(summarizer.maybe_summarize(session_id))
        _spawn(summarizer.generate_title(session_id, question, final_answer))

    try:
        while True:
            try:
                kind, payload = await asyncio.wait_for(
                    queue.get(), timeout=HEARTBEAT_INTERVAL
                )
            except asyncio.TimeoutError:
                if await request.is_disconnected():
                    disconnected = True
                    break
                yield ": heartbeat\n\n"
                continue

            if kind == "done":
                break
            if kind == "error":
                raise payload

            if payload["type"] == "tool_end":
                trace_events.append(payload["data"])
            elif payload["type"] == "final_answer":
                final_answer = payload["data"].get("answer", "")

            line = json.dumps(payload, ensure_ascii=False)
            yield f"data: {line}\n\n"

        if not disconnected:
            yield "data: [DONE]\n\n"
        await _finalize()
    except Exception:
        logger.exception("SSE stream failed [req=%s] for question: %s", req_id, question[:200])
        err = json.dumps(
            {"type": "error", "data": {"message": "服务器内部错误，请稍后重试"}},
            ensure_ascii=False,
        )
        yield f"data: {err}\n\n"
        await _finalize()
    finally:
        if not producer.done():
            producer.cancel()
        # 客户端强断开（GeneratorExit/CancelledError 不经 except Exception）时
        # 兜底：fire-and-forget，不 await（此时无法安全 await）
        if user_id and session_id and not persisted:
            _spawn(
                _persist_turn(
                    session_id, question, final_answer or "（本轮回答未完成）", trace_events
                )
            )


@router.post("")
async def chat(body: ChatRequest, request: Request) -> StreamingResponse:
    """Send a question and receive agent execution steps as SSE events.

    Public endpoint (no auth).  Rate-limited per client IP (hourly) with a
    site-wide daily cap as an anti-abuse backstop.  Each SSE event is a JSON
    object with ``type``, ``node``, and ``data`` fields.  The stream ends
    with ``data: [DONE]``.
    """
    client_ip = get_client_ip(request)
    check_rate_limit(client_ip)       # 先查 IP：被拒请求不消耗全局名额
    check_global_daily_cap()

    user_id = get_user_id_optional(request)
    session_id: str | None = None
    history_text = ""
    extra_headers: dict[str, str] = {}

    if user_id:
        if body.session_id:
            sess = await asyncio.to_thread(session_store.get_session, body.session_id)
            if sess is None:
                raise HTTPException(status_code=404, detail="会话不存在")
            if sess["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="无权访问该会话")
            session_id = body.session_id
            ctx = await asyncio.to_thread(
                session_store.get_memory_context, session_id, settings.memory_recent_turns
            )
            history_text = summarizer.build_history_text(ctx)
        else:
            # 兼容路径：隐式新建（仅老前端/裸调用；新前端应先 POST /api/sessions）
            session_id = await asyncio.to_thread(session_store.create_session, user_id)
            extra_headers["X-Session-Id"] = session_id

    return StreamingResponse(
        _event_generator(
            body.question,
            request,
            user_id=user_id,
            session_id=session_id,
            history_text=history_text,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable Nginx buffering
            **extra_headers,
        },
    )
