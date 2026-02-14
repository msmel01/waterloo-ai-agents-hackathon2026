"""Task enqueue helpers for background scoring flows."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def enqueue_scoring_job(session_id: str) -> None:
    """Stub enqueue hook for M5 scoring pipeline."""
    logger.info("[STUB] Scoring job enqueued for session: %s", session_id)
    # Future M5 implementation:
    # await arq_pool.enqueue_job("score_session", session_id)
