"""Session endpoints."""

import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from src.core.container import Container
from src.models.domain_enums import SessionStatus
from src.repository.heart_repository import HeartRepository
from src.repository.score_repository import ScoreRepository
from src.repository.session_repository import SessionRepository
from src.repository.suitor_repository import SuitorRepository
from src.schemas.session_schema import (
    SessionStartRequest,
    SessionStartResponse,
    SessionStatusResponse,
    SessionVerdictResponse,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])

HeartRepoDep = Annotated[HeartRepository, Depends(Provide[Container.heart_repository])]
SuitorRepoDep = Annotated[
    SuitorRepository, Depends(Provide[Container.suitor_repository])
]
SessionRepoDep = Annotated[
    SessionRepository, Depends(Provide[Container.session_repository])
]
ScoreRepoDep = Annotated[ScoreRepository, Depends(Provide[Container.score_repository])]


@router.post(
    "/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED
)
@inject
async def start_session(
    payload: SessionStartRequest,
    heart_repo: HeartRepoDep,
    suitor_repo: SuitorRepoDep,
    session_repo: SessionRepoDep,
):
    """Initialize a new interview session for a suitor and heart."""
    heart = await heart_repo.find_by_slug(payload.heart_slug)
    if not heart or not heart.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Heart link not found"
        )

    suitor = await suitor_repo.read_by_id(payload.suitor_id)
    if not suitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Suitor not found"
        )

    created = await session_repo.create(
        session_repo.model(
            heart_id=heart.id,
            suitor_id=suitor.id,
            status=SessionStatus.PENDING,
            livekit_room_name=f"vh_{heart.id}_{suitor.id}"[:255],
        )
    )

    return SessionStartResponse(
        session_id=created.id,
        heart_id=created.heart_id,
        suitor_id=created.suitor_id,
        status=created.status,
        livekit_room_name=created.livekit_room_name,
        livekit_token=None,
        created_at=created.created_at,
    )


@router.get("/{id}/status", response_model=SessionStatusResponse)
@inject
async def get_session_status(id: uuid.UUID, session_repo: SessionRepoDep):
    """Get current processing state for a session."""
    session = await session_repo.read_by_id(id)
    return SessionStatusResponse(
        session_id=session.id,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
    )


@router.get("/{id}/verdict", response_model=SessionVerdictResponse)
@inject
async def get_session_verdict(
    id: uuid.UUID,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
):
    """Poll final verdict and score breakdown for a completed session."""
    session = await session_repo.read_by_id(id)
    score = await score_repo.find_by_session_id(session.id)

    if not score:
        return SessionVerdictResponse(session_id=session.id, ready=False)

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
        ready=True,
    )
