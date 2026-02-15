"""Task enqueue helpers for background scoring flows."""

from __future__ import annotations

import logging

from arq import create_pool
from arq.connections import RedisSettings

from src.core.config import config

logger = logging.getLogger(__name__)


async def enqueue_scoring_job(session_id: str) -> None:
    """Enqueue the score_session_task worker job."""
    redis = await create_pool(RedisSettings.from_dsn(config.REDIS_URL))
    try:
        await redis.enqueue_job("score_session_task", session_id, _defer_by=5)
        logger.info("Scoring job enqueued for session: %s", session_id)
    finally:
        await redis.aclose()
