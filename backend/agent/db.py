"""Database bridge for the standalone LiveKit agent process."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import select

from src.core.config import config
from src.models.conversation_turn_model import ConversationTurnDb
from src.models.domain_enums import ConversationSpeaker, SessionStatus
from src.models.heart_model import HeartDb
from src.models.screening_question_model import ScreeningQuestionDb
from src.models.session_model import SessionDb
from src.models.suitor_model import SuitorDb

engine = create_async_engine(config.SQLALCHEMY_DATABASE_URI, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_heart_config() -> dict:
    """Load active heart profile + screening questions into one config payload."""
    async with AsyncSessionLocal() as db:
        heart_result = await db.execute(
            select(HeartDb).order_by(HeartDb.created_at.desc()).limit(1)
        )
        heart = heart_result.scalars().first()
        if not heart:
            raise RuntimeError("No Heart profile found in database")

        questions_result = await db.execute(
            select(ScreeningQuestionDb)
            .where(ScreeningQuestionDb.heart_id == heart.id)
            .order_by(ScreeningQuestionDb.order_index.asc())
        )
        questions = questions_result.scalars().all()

        return {
            "id": str(heart.id),
            "profile": {
                "display_name": heart.display_name,
                "bio": heart.bio,
                "photo_url": heart.photo_url,
                "video_url": heart.video_url,
            },
            "persona": heart.persona or {},
            "expectations": heart.expectations or {},
            "screening_questions": [
                {
                    "text": question.question_text,
                    "required": question.is_required,
                    "order_index": question.order_index,
                }
                for question in questions
            ],
            "shareable_slug": heart.shareable_slug,
            "tavus_replica_id": heart.tavus_avatar_id,
            "calcom_event_type_id": heart.calcom_event_type_id,
        }


async def get_session_by_room(session_id: str) -> dict | None:
    """Load one session and suitor profile by room/session ID."""
    async with AsyncSessionLocal() as db:
        session_uuid = uuid.UUID(session_id)
        result = await db.execute(select(SessionDb).where(SessionDb.id == session_uuid))
        session = result.scalars().first()
        if not session:
            return None

        suitor_result = await db.execute(
            select(SuitorDb).where(SuitorDb.id == session.suitor_id)
        )
        suitor = suitor_result.scalars().first()
        suitor_name = suitor.name if suitor else "Suitor"

        return {
            "session_id": str(session.id),
            "heart_id": str(session.heart_id),
            "suitor_id": str(session.suitor_id),
            "suitor_name": suitor_name,
            "room_name": session.livekit_room_name,
            "status": session.status.value,
        }


async def update_session_status(session_id: str, status: str) -> None:
    """Update one session status from agent process."""
    status_map = {
        "pending": SessionStatus.PENDING,
        "in_progress": SessionStatus.IN_PROGRESS,
        "completed": SessionStatus.COMPLETED,
        "failed": SessionStatus.FAILED,
        "cancelled": SessionStatus.CANCELLED,
    }
    target_status = status_map.get(status)
    if not target_status:
        raise ValueError(f"Unsupported session status: {status}")

    async with AsyncSessionLocal() as db:
        session_uuid = uuid.UUID(session_id)
        result = await db.execute(select(SessionDb).where(SessionDb.id == session_uuid))
        session = result.scalars().first()
        if not session:
            raise RuntimeError(f"Session not found: {session_id}")
        session.status = target_status
        if target_status == SessionStatus.IN_PROGRESS and session.started_at is None:
            session.started_at = datetime.now(timezone.utc)
        db.add(session)
        await db.commit()


async def save_conversation_data(session_id: str, session_data: dict) -> None:
    """Persist transcript data and mark session complete, then enqueue scoring job."""
    async with AsyncSessionLocal() as db:
        session_uuid = uuid.UUID(session_id)
        result = await db.execute(select(SessionDb).where(SessionDb.id == session_uuid))
        session = result.scalars().first()
        if not session:
            raise RuntimeError(f"Session not found: {session_id}")

        transcript = session_data.get("full_transcript", [])
        for index, turn in enumerate(transcript):
            speaker_value = (turn.get("speaker") or "avatar").lower()
            speaker = (
                ConversationSpeaker.SUITOR
                if speaker_value == "suitor"
                else ConversationSpeaker.AVATAR
            )
            db.add(
                ConversationTurnDb(
                    session_id=session_uuid,
                    turn_index=index,
                    speaker=speaker,
                    content=turn.get("text", ""),
                    emotion_data=turn.get("emotions"),
                    duration_seconds=turn.get("duration"),
                )
            )

        started_at_ts = session_data.get("started_at")
        ended_at_ts = session_data.get("ended_at")

        if started_at_ts:
            session.started_at = datetime.fromtimestamp(started_at_ts, tz=timezone.utc)
        if ended_at_ts:
            session.ended_at = datetime.fromtimestamp(ended_at_ts, tz=timezone.utc)
        else:
            session.ended_at = datetime.now(timezone.utc)
        session.status = SessionStatus.COMPLETED
        db.add(session)
        await db.commit()

    await enqueue_scoring_job(session_id)


async def enqueue_scoring_job(session_id: str) -> None:
    """Queue async scoring pipeline job (implemented in M5)."""
    redis_pool = await create_pool(RedisSettings.from_dsn(config.REDIS_URL))
    try:
        await redis_pool.enqueue_job("score_session", session_id)
    finally:
        await redis_pool.aclose()
