"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import logging.config
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/api/health/ready")
async def ready() -> dict:
    """Readiness check — verifies that the LLM API key is configured."""
    if not settings.deepseek_api_key:
        return {"status": "not ready", "reason": "DEEPSEEK_API_KEY not configured"}
    return {"status": "ok"}
