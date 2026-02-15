"""Task enqueue helpers for background scoring flows."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from arq import create_pool
from arq.connections import RedisSettings

from src.core.config import config
from src.core.database import Database
from src.models.session_model import SessionDb

logger = logging.getLogger(__name__)
database = Database(config)


async def enqueue_scoring_job(session_id: str) -> None:
    """Enqueue the score_session_task worker job."""
    redis = await create_pool(RedisSettings.from_dsn(config.REDIS_URL))
    try:
        await redis.enqueue_job("score_session_task", session_id, _defer_by=5)
        logger.info("Scoring job enqueued for session: %s", session_id)
    except Exception as exc:
        logger.exception("Failed to enqueue scoring job for session %s", session_id)
        async with database.session() as session:
            db_session = await session.get(SessionDb, uuid.UUID(session_id))
            if db_session is not None:
                metadata = dict(db_session.session_metadata or {})
                metadata["scoring_pending"] = True
                metadata["scoring_pending_reason"] = str(exc)
                metadata["scoring_pending_at"] = datetime.now(timezone.utc).isoformat()
                db_session.session_metadata = metadata
                session.add(db_session)
                await session.commit()
    finally:
        await redis.aclose()
