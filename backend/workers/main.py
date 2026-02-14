"""arq worker entrypoint and placeholder background tasks."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from arq import cron
from arq.connections import RedisSettings
from sqlmodel import select

from src.core.config import config
from src.core.database import Database
from src.models.domain_enums import SessionStatus
from src.models.heart_model import HeartDb
from src.models.session_model import SessionDb
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


async def cleanup_stale_sessions(ctx: dict) -> dict[str, int]:
    """Expire stale pending/in-progress sessions to keep interview state healthy."""
    _ = ctx
    now = datetime.now(timezone.utc)
    pending_cutoff = now - timedelta(seconds=config.SESSION_PENDING_TIMEOUT)
    in_progress_cutoff = now - timedelta(seconds=config.SESSION_MAX_DURATION)

    expired_pending = 0
    expired_in_progress = 0

    async with database.session() as session:
        pending_result = await session.execute(
            select(SessionDb).where(
                SessionDb.status == SessionStatus.PENDING,
                SessionDb.created_at < pending_cutoff,
            )
        )
        for stale in pending_result.scalars().all():
            stale.status = SessionStatus.EXPIRED
            stale.end_reason = "connection_timeout"
            stale.ended_at = now
            session.add(stale)
            expired_pending += 1

        progress_result = await session.execute(
            select(SessionDb).where(
                SessionDb.status == SessionStatus.IN_PROGRESS,
                SessionDb.started_at.is_not(None),
                SessionDb.started_at < in_progress_cutoff,
            )
        )
        for stale in progress_result.scalars().all():
            stale.status = SessionStatus.EXPIRED
            stale.end_reason = "max_duration_exceeded"
            stale.ended_at = now
            session.add(stale)
            expired_in_progress += 1

        await session.commit()

    if expired_pending or expired_in_progress:
        logger.info(
            "Expired stale sessions pending=%s in_progress=%s",
            expired_pending,
            expired_in_progress,
        )

    return {
        "expired_pending": expired_pending,
        "expired_in_progress": expired_in_progress,
    }


class WorkerSettings:
    """arq worker configuration."""

    redis_settings = RedisSettings.from_dsn(config.REDIS_URL)
    functions = [
        score_session,
        generate_tavus_avatar,
        send_notification,
        poll_tavus_replica_status,
        cleanup_stale_sessions,
    ]
    cron_jobs = [
        cron(
            cleanup_stale_sessions,
            minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55},
        ),
    ]
    job_timeout = 300
    keep_result = 3600
