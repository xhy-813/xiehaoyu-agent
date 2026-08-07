"""定时清理过期/超量会话（设计文档 §8）。

单 worker 部署（现状）下由 lifespan 启动一个协程；
若未来改多 worker，需移到独立 cron 或加分布式锁。
"""

from __future__ import annotations

import asyncio
import logging

from backend.app.services import session_store
from configs.settings import settings

logger = logging.getLogger(__name__)


async def cleanup_loop() -> None:
    """启动时立即清理一轮，之后每 MEMORY_CLEANUP_INTERVAL_HOURS 小时一轮。

    通过 task.cancel() 停止（asyncio.sleep / to_thread 处抛 CancelledError）。
    """
    while True:
        try:
            result = await asyncio.to_thread(
                session_store.cleanup,
                settings.memory_max_age_days,
                settings.memory_max_sessions_per_user,
            )
            if result["aged_out"] or result["overflow_deleted"]:
                logger.info("Session cleanup done: %s", result)
        except Exception:
            logger.exception("Session cleanup failed")
        await asyncio.sleep(settings.memory_cleanup_interval_hours * 3600)
