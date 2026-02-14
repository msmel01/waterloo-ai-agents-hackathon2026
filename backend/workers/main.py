"""arq worker entrypoint and placeholder background tasks."""

from __future__ import annotations

import asyncio
import logging
import uuid

from arq.connections import RedisSettings
from sqlmodel import select

from src.core.config import config
from src.core.database import Database
from src.models.heart_model import HeartDb
from src.services.tavus_service import TavusService

logger = logging.getLogger(__name__)
database = Database(config)


async def score_session(ctx: dict, session_id: str) -> None:
    """Placeholder task for Claude-based session scoring."""
    _ = (ctx, session_id)


async def generate_tavus_avatar(ctx: dict, heart_id: str) -> None:
    """Placeholder task for Tavus avatar generation."""
    _ = (ctx, heart_id)


async def send_notification(ctx: dict, heart_id: str, event_type: str) -> None:
    """Placeholder task for heart notifications."""
    _ = (ctx, heart_id, event_type)


async def poll_tavus_replica_status(ctx: dict, heart_id: str, replica_id: str) -> dict:
    """Poll Tavus replica status until ready/failed or timeout."""
    _ = ctx
    if not config.TAVUS_API_KEY:
        logger.error("TAVUS_API_KEY is not configured; cannot poll replica status")
        return {"status": "failed", "replica_id": replica_id}

    tavus = TavusService(config.TAVUS_API_KEY.get_secret_value())
    max_attempts = 30

    for attempt in range(max_attempts):
        try:
            payload = await tavus.get_replica(replica_id)
            status = str(payload.get("status", "")).lower()

            if status == "ready":
                async with database.session() as session:
                    query = select(HeartDb).where(HeartDb.id == uuid.UUID(heart_id))
                    result = await session.execute(query)
                    heart = result.scalars().first()
                    if heart:
                        heart.tavus_avatar_id = replica_id
                        session.add(heart)
                        await session.commit()
                logger.info("Tavus replica %s is ready", replica_id)
                return {"status": "ready", "replica_id": replica_id}

            if status in {"error", "failed"}:
                logger.error("Tavus replica %s failed: %s", replica_id, payload)
                return {"status": "failed", "replica_id": replica_id}

            logger.info(
                "Tavus replica %s status=%s (%s/%s)",
                replica_id,
                status or "unknown",
                attempt + 1,
                max_attempts,
            )
        except Exception as exc:
            logger.error(
                "Error polling Tavus replica %s on attempt %s: %s",
                replica_id,
                attempt + 1,
                exc,
            )

        await asyncio.sleep(60)

    logger.error("Tavus replica %s polling timed out", replica_id)
    return {"status": "timeout", "replica_id": replica_id}


class WorkerSettings:
    """arq worker configuration."""

    redis_settings = RedisSettings.from_dsn(config.REDIS_URL)
    functions = [
        score_session,
        generate_tavus_avatar,
        send_notification,
        poll_tavus_replica_status,
    ]
    job_timeout = 300
    keep_result = 3600
