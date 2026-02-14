"""Session endpoints."""

import json
import uuid
from datetime import datetime, timezone
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from src.core.config import config
from src.core.container import Container
from src.core.exceptions import NotFoundError
from src.dependencies import get_current_suitor, get_livekit_service
from src.models.domain_enums import SessionStatus
from src.models.suitor_model import SuitorDb
from src.repository.heart_repository import HeartRepository
from src.repository.score_repository import ScoreRepository
from src.repository.session_repository import SessionRepository
from src.schemas.common_schema import SuccessResponse
from src.schemas.session_schema import (
    SessionStartRequest,
    SessionStartResponse,
    SessionStatusResponse,
    SessionVerdictResponse,
)
from src.services.livekit_service import LiveKitService

router = APIRouter(prefix="/sessions", tags=["Sessions"])

CurrentSuitor = Annotated[SuitorDb, Depends(get_current_suitor)]
HeartRepoDep = Annotated[HeartRepository, Depends(Provide[Container.heart_repository])]
SessionRepoDep = Annotated[
    SessionRepository, Depends(Provide[Container.session_repository])
]
ScoreRepoDep = Annotated[ScoreRepository, Depends(Provide[Container.score_repository])]
LiveKitDep = Annotated[LiveKitService, Depends(get_livekit_service)]
AGENT_NAME = "valentine-interview-agent"


@router.post(
    "/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED
)
@inject
async def start_session(
    payload: SessionStartRequest,
    suitor: CurrentSuitor,
    heart_repo: HeartRepoDep,
    session_repo: SessionRepoDep,
    livekit: LiveKitDep,
):
    """Start a new interview session and return LiveKit join credentials."""
    if suitor.age is None or suitor.gender is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete your profile first (age, gender required)",
        )

    heart = await heart_repo.find_by_slug(payload.heart_slug)
    if not heart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Heart link not found"
        )
    if not heart.is_active:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This Heart link is currently inactive",
        )
    if not heart.tavus_avatar_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Avatar is not ready yet. Try again later.",
        )

    active = await session_repo.find_active_by_suitor(suitor.id)
    if active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active session",
        )

    draft = session_repo.model(
        heart_id=heart.id,
        suitor_id=suitor.id,
        status=SessionStatus.PENDING,
        livekit_room_name=None,
    )
    created = await session_repo.create(draft)
    room_name = f"session-{created.id}"
    created = await session_repo.update_attr(created.id, "livekit_room_name", room_name)

    room_metadata = json.dumps(
        {
            "session_id": str(created.id),
            "heart_id": str(heart.id),
            "suitor_id": str(suitor.id),
        }
    )
    try:
        room = await livekit.create_room(
            room_name=room_name,
            max_participants=3,
            metadata=room_metadata,
        )
        await livekit.create_agent_dispatch(
            room_name=room_name,
            agent_name=AGENT_NAME,
            metadata=room_metadata,
        )
        await session_repo.update_attr(created.id, "livekit_room_sid", room.get("sid"))
        suitor_name = suitor.name or "Suitor"
        livekit_token = livekit.generate_suitor_token(
            room_name=room_name,
            suitor_id=str(suitor.id),
            suitor_name=suitor_name,
        )
    except Exception as exc:
        await session_repo.update_status(created.id, SessionStatus.FAILED)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to initialize LiveKit room: {exc}",
        )
    finally:
        await livekit.close()

    return SessionStartResponse(
        session_id=created.id,
        livekit_url=config.LIVEKIT_URL or "",
        livekit_token=livekit_token,
        room_name=room_name,
    )


@router.get("/{id}/status", response_model=SessionStatusResponse)
@inject
async def get_session_status(
    id: uuid.UUID,
    suitor: CurrentSuitor,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
):
    """Get current processing state for a session owned by the authenticated suitor."""
    try:
        session = await session_repo.read_by_id(id)
    except NotFoundError:
        session = None
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.suitor_id != suitor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    score = await score_repo.find_by_session_id(session.id)
    status_value = session.status.value
    if session.status == SessionStatus.COMPLETED:
        status_value = "scoring"
    if score:
        status_value = "scored"

    duration_seconds = None
    if session.started_at:
        end_ref = session.ended_at or datetime.now(timezone.utc)
        duration_seconds = max(0.0, (end_ref - session.started_at).total_seconds())

    return SessionStatusResponse(
        session_id=session.id,
        status=status_value,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_seconds=duration_seconds,
    )


@router.post("/{id}/end", response_model=SuccessResponse)
@inject
async def end_session(
    id: uuid.UUID,
    suitor: CurrentSuitor,
    session_repo: SessionRepoDep,
    livekit: LiveKitDep,
):
    """End an active session and clean up the LiveKit room."""
    try:
        session = await session_repo.read_by_id(id)
    except NotFoundError:
        session = None
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.suitor_id != suitor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    now = datetime.now(timezone.utc)
    await session_repo.update_attr(id, "ended_at", now)
    await session_repo.update_attr(id, "end_reason", "manual_end")
    if session.status in {SessionStatus.PENDING, SessionStatus.IN_PROGRESS}:
        await session_repo.update_status(id, SessionStatus.COMPLETED)

    if session.livekit_room_name:
        try:
            await livekit.delete_room(session.livekit_room_name)
        finally:
            await livekit.close()

    return SuccessResponse(message="Session ended")


@router.get("/{id}/verdict", response_model=SessionVerdictResponse)
@inject
async def get_session_verdict(
    id: uuid.UUID,
    suitor: CurrentSuitor,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
):
    """Get verdict and score breakdown for a completed/scored session."""
    try:
        session = await session_repo.read_by_id(id)
    except NotFoundError:
        session = None
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.suitor_id != suitor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    score = await score_repo.find_by_session_id(session.id)

    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session has not been scored yet",
        )

    return SessionVerdictResponse(
        session_id=session.id,
        verdict=score.verdict,
        weighted_total=score.weighted_total,
        effort_score=score.effort_score,
        creativity_score=score.creativity_score,
        intent_clarity_score=score.intent_clarity_score,
        emotional_intelligence_score=score.emotional_intelligence_score,
        emotion_modifiers=score.emotion_modifiers,
        feedback_text=score.feedback_text,
    )
