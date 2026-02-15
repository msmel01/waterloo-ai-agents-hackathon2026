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
from src.core.exceptions import DuplicatedError, NotFoundError
from src.models.domain_enums import SessionStatus
from src.models.heart_model import HeartDb
from src.models.score_model import ScoreDb
from src.models.session_model import SessionDb
from src.models.suitor_model import SuitorDb
from src.repository.conversation_turn_repository import ConversationTurnRepository
from src.repository.score_repository import ScoreRepository
from src.repository.session_repository import SessionRepository
from src.services.config_loader import HeartConfigLoader
from src.services.tavus_service import TavusService

logger = logging.getLogger(__name__)
database = Database(config)


def _to_heart_config_payload(loaded: HeartConfigLoader) -> dict:
    cfg = loaded.config
    if cfg is None:
        raise RuntimeError("Heart config is not loaded")
    return {
        "display_name": cfg.profile.display_name,
        "bio": cfg.profile.bio,
        "persona": cfg.persona.model_dump(),
        "expectations": cfg.expectations.model_dump(),
        "screening_questions": [q.model_dump() for q in cfg.screening_questions],
    }


async def score_session_task(ctx: dict, session_id: str) -> None:
    """Score completed interview with Claude and persist verdict."""
    _ = ctx
    session_uuid = uuid.UUID(session_id)
    session_repo = SessionRepository(session_factory=database.session)
    score_repo = ScoreRepository(session_factory=database.session)
    turn_repo = ConversationTurnRepository(session_factory=database.session)

    try:
        session = await session_repo.read_by_id(session_uuid)
    except NotFoundError:
        logger.warning("Skipping scoring; session %s was not found", session_id)
        return
    if session.status not in {SessionStatus.COMPLETED, SessionStatus.SCORING}:
        logger.info(
            "Skipping scoring for session %s with status=%s", session_id, session.status
        )
        return

    if await score_repo.exists_for_session(session_uuid):
        logger.info(
            "Skipping scoring for session %s because score already exists", session_id
        )
        await session_repo.update_attr(session_uuid, "has_verdict", True)
        await session_repo.update_attr(session_uuid, "verdict_status", "ready")
        if session.status != SessionStatus.SCORED:
            await session_repo.update_status(session_uuid, SessionStatus.SCORED)
        return

    await session_repo.update_status(session_uuid, SessionStatus.SCORING)
    await session_repo.update_attr(session_uuid, "verdict_status", "scoring")
    await session_repo.update_attr(session_uuid, "has_verdict", False)

    try:
        loader = HeartConfigLoader()
        loader.load()
        heart_config = _to_heart_config_payload(loader)

        turns = await turn_repo.find_by_session_id(session_uuid)
        transcript = [
            {
                "turn_index": turn.turn_index,
                "speaker": turn.speaker.value.lower(),
                "content": turn.content,
                "timestamp": (
                    turn.created_at.isoformat()
                    if getattr(turn, "created_at", None)
                    else None
                ),
            }
            for turn in turns
        ]

        turn_summaries_raw = session.turn_summaries or {}
        if isinstance(turn_summaries_raw, dict):
            turn_summaries = turn_summaries_raw.get("turns", []) or []
        else:
            turn_summaries = []
        if not isinstance(turn_summaries, list):
            turn_summaries = []

        from src.services.scoring.scoring_service import ScoringService

        scoring_service = ScoringService()
        score_payload = await scoring_service.score_session(
            heart_config=heart_config,
            session_data={
                "session_id": str(session.id),
                "suitor_id": str(session.suitor_id),
                "heart_id": str(session.heart_id),
                "started_at": session.started_at.isoformat()
                if session.started_at
                else None,
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "end_reason": session.end_reason,
            },
            turn_summaries=turn_summaries,
            transcript=transcript,
        )
        score_payload["session_id"] = session_uuid
        try:
            await score_repo.create(score_payload)
        except DuplicatedError:
            if await score_repo.exists_for_session(session_uuid):
                logger.info(
                    "Duplicate score write detected for session %s; treating as idempotent success",
                    session_id,
                )
                await session_repo.update_attr(session_uuid, "has_verdict", True)
                await session_repo.update_attr(session_uuid, "verdict_status", "ready")
                await session_repo.update_status(session_uuid, SessionStatus.SCORED)
                return
            raise

        await session_repo.update_attr(session_uuid, "has_verdict", True)
        await session_repo.update_attr(session_uuid, "verdict_status", "ready")
        await session_repo.update_status(session_uuid, SessionStatus.SCORED)
        logger.info(
            "Session %s scored successfully (final_score=%s, verdict=%s)",
            session_id,
            score_payload.get("final_score"),
            score_payload.get("verdict"),
        )
    except Exception:
        logger.exception("Session scoring failed for %s", session_id)
        await session_repo.update_attr(session_uuid, "has_verdict", False)
        await session_repo.update_attr(session_uuid, "verdict_status", "failed")
        await session_repo.update_status(session_uuid, SessionStatus.FAILED)
        raise


async def score_session(ctx: dict, session_id: str) -> None:
    """Backward-compatible alias for the scoring task name."""
    await score_session_task(ctx, session_id)


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

    repo = SessionRepository(session_factory=database.session)
    stale_pending = await repo.find_stale_pending(pending_cutoff)
    stale_in_progress = await repo.find_stale_in_progress(in_progress_cutoff)

    for stale in stale_pending:
        await repo.update_status(stale.id, SessionStatus.EXPIRED)
        await repo.update_attr(stale.id, "end_reason", "connection_timeout")
        await repo.update_attr(stale.id, "ended_at", now)

    for stale in stale_in_progress:
        await repo.update_status(stale.id, SessionStatus.EXPIRED)
        await repo.update_attr(stale.id, "end_reason", "max_duration_exceeded")
        await repo.update_attr(stale.id, "ended_at", now)

    expired_pending = len(stale_pending)
    expired_in_progress = len(stale_in_progress)

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


async def cleanup_old_data(ctx: dict) -> dict[str, int]:
    """Daily retention cleanup: anonymize old completed data and delete stale failures."""
    _ = ctx
    retention_cutoff = datetime.now(timezone.utc) - timedelta(
        days=config.DATA_RETENTION_DAYS
    )
    orphan_cutoff = datetime.now(timezone.utc) - timedelta(days=7)

    async with database.session() as session:
        failed_query = select(SessionDb).where(
            SessionDb.status == SessionStatus.FAILED,
            SessionDb.created_at < retention_cutoff,
        )
        failed_sessions = (await session.execute(failed_query)).scalars().all()
        for item in failed_sessions:
            await session.delete(item)

        completed_query = select(SessionDb).where(
            SessionDb.status.in_(
                [SessionStatus.COMPLETED, SessionStatus.SCORING, SessionStatus.SCORED]
            ),
            SessionDb.created_at < retention_cutoff,
        )
        completed_sessions = (await session.execute(completed_query)).scalars().all()
        for item in completed_sessions:
            item.turn_summaries = None
            metadata = dict(item.session_metadata or {})
            metadata["retention"] = {
                "anonymized_at": datetime.now(timezone.utc).isoformat(),
                "policy_days": config.DATA_RETENTION_DAYS,
            }
            item.session_metadata = metadata
            session.add(item)

        orphan_query = select(SuitorDb).where(SuitorDb.created_at < orphan_cutoff)
        orphans = (await session.execute(orphan_query)).scalars().all()
        orphan_count = 0
        for suitor in orphans:
            has_session = bool(
                (
                    await session.execute(
                        select(SessionDb.id)
                        .where(SessionDb.suitor_id == suitor.id)
                        .limit(1)
                    )
                ).first()
            )
            if has_session:
                continue
            await session.delete(suitor)
            orphan_count += 1

        await session.commit()

    logger.info(
        "Retention cleanup complete failed_deleted=%s completed_anonymized=%s orphans_deleted=%s",
        len(failed_sessions),
        len(completed_sessions),
        orphan_count,
    )
    return {
        "failed_deleted": len(failed_sessions),
        "completed_anonymized": len(completed_sessions),
        "orphans_deleted": orphan_count,
    }


async def retry_pending_scoring(ctx: dict) -> dict[str, int]:
    """Retry scoring for completed sessions that still don't have scores."""
    _ = ctx
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    retried = 0

    async with database.session() as session:
        pending_query = (
            select(SessionDb)
            .outerjoin(ScoreDb, ScoreDb.session_id == SessionDb.id)
            .where(
                SessionDb.status.in_([SessionStatus.COMPLETED, SessionStatus.SCORING]),
                ScoreDb.id.is_(None),
                SessionDb.ended_at.is_not(None),
                SessionDb.ended_at < cutoff,
            )
            .limit(50)
        )
        pending = (await session.execute(pending_query)).scalars().all()

    for candidate in pending:
        try:
            await score_session_task({}, str(candidate.id))
            retried += 1
        except Exception:
            logger.exception("Retry scoring failed for session %s", candidate.id)

    return {"retried": retried}


class WorkerSettings:
    """arq worker configuration."""

    redis_settings = RedisSettings.from_dsn(config.REDIS_URL)
    functions = [
        score_session,
        score_session_task,
        generate_tavus_avatar,
        send_notification,
        poll_tavus_replica_status,
        cleanup_stale_sessions,
        cleanup_old_data,
        retry_pending_scoring,
    ]
    cron_jobs = [
        cron(
            cleanup_stale_sessions,
            minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55},
        ),
        cron(retry_pending_scoring, minute={2, 12, 22, 32, 42, 52}),
        cron(cleanup_old_data, hour={3}, minute={0}),
    ]
    max_tries = 3
    job_timeout = 300
    keep_result = 3600
