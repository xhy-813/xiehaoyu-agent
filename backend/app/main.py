"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import logging.config
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Structured logging configuration ────────────────────────

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)-5s %(name)s | %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stderr,
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        "agent": {"level": "INFO", "handlers": ["console"], "propagate": False},
        "rag": {"level": "INFO", "handlers": ["console"], "propagate": False},
        "backend": {"level": "INFO", "handlers": ["console"], "propagate": False},
        "chatbi": {"level": "INFO", "handlers": ["console"], "propagate": False},
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Ensure the project root is on sys.path so agent / configs / chatbi / rag
# can be imported from the backend sub-package.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from configs.settings import settings  # noqa: E402
from agent.llm_client import get_client  # noqa: E402
from backend.app.routers import chat, sessions  # noqa: E402
from backend.app.services import cleanup, session_store  # noqa: E402

@asynccontextmanager
async def lifespan(app: FastAPI):
    session_store.init_store()
    cleanup_task = asyncio.create_task(cleanup.cleanup_loop())
    yield
    cleanup_task.cancel()


app = FastAPI(
    title="Xiehaoyu-Agent API",
    description="个人智能体与 ChatBI 系统后端",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS (allow frontend dev server) ──────────────────────
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-User-Id"],
)

# ── Routers ───────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(sessions.router)


@app.get("/api/health")
async def health() -> dict:
    """Liveness check."""
    return {"status": "ok"}


# 808 审查 M14：就绪探活结果缓存 60s（models.list 不计费，但避免探活本身成为流量放大器）
_ready_probe: dict = {"ts": 0.0, "ok": False}


@app.get("/api/health/ready")
async def ready():
    """Readiness check — key 非空 + DeepSeek API 轻量探活（GET /models，60s 缓存）。"""
    if not settings.deepseek_api_key:
        return JSONResponse(
            {"status": "not ready", "reason": "DEEPSEEK_API_KEY not configured"},
            status_code=503,
        )

    now = time.time()
    if now - _ready_probe["ts"] < 60:
        ok = _ready_probe["ok"]
    else:
        try:
            client = get_client()
            await asyncio.to_thread(client.models.list)
            ok = True
        except Exception:
            logger.exception("Readiness probe to DeepSeek API failed")
            ok = False
        _ready_probe.update(ts=now, ok=ok)

    if ok:
        return {"status": "ok"}
    return JSONResponse(
        {"status": "not ready", "reason": "DeepSeek API unreachable"}, status_code=503
    )
