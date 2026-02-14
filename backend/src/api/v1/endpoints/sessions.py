"""Session endpoints."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.core.config import config
from src.core.container import Container
from src.core.exceptions import NotFoundError
from src.dependencies import (
    get_current_suitor,
    get_current_suitor_optional,
    get_livekit_service,
)
from src.models.domain_enums import SessionStatus
from src.models.suitor_model import SuitorDb
from src.repository.heart_repository import HeartRepository
from src.repository.score_repository import ScoreRepository
from src.repository.session_repository import SessionRepository
from src.repository.suitor_repository import SuitorRepository
from src.schemas.common_schema import SuccessResponse
from src.schemas.session_schema import (
    PreCheckResponse,
    SessionStartRequest,
    SessionStartResponse,
    SessionStatusResponse,
    SessionVerdictResponse,
)
from src.services.livekit_service import LiveKitService

router = APIRouter(prefix="/sessions", tags=["Sessions"])
logger = logging.getLogger(__name__)

try:
    from livekit.api import TwirpError
except ImportError:  # pragma: no cover - optional dependency guard
    TwirpError = RuntimeError  # type: ignore[assignment]

CurrentSuitor = Annotated[SuitorDb, Depends(get_current_suitor)]
OptionalSuitor = Annotated[SuitorDb | None, Depends(get_current_suitor_optional)]
HeartRepoDep = Annotated[HeartRepository, Depends(Provide[Container.heart_repository])]
SessionRepoDep = Annotated[
    SessionRepository, Depends(Provide[Container.session_repository])
]
ScoreRepoDep = Annotated[ScoreRepository, Depends(Provide[Container.score_repository])]
SuitorRepoDep = Annotated[
    SuitorRepository, Depends(Provide[Container.suitor_repository])
]
LiveKitDep = Annotated[LiveKitService, Depends(get_livekit_service)]
AGENT_NAME = "valentine-interview-agent"


@router.post(
    "/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED
)
@inject
async def start_session(
    payload: SessionStartRequest,
    suitor: OptionalSuitor,
    suitor_repo: SuitorRepoDep,
    heart_repo: HeartRepoDep,
    session_repo: SessionRepoDep,
    livekit: LiveKitDep,
):
    """Start a new interview session and return LiveKit join credentials."""
    if suitor is None:
        # Temporary local-dev bypass when JWT auth is not wired yet.
        suitor = await suitor_repo.find_by_clerk_id("local-dev-suitor")
        if not suitor:
            suitor = await suitor_repo.create(
                suitor_repo.model(
                    clerk_user_id="local-dev-suitor",
                    name="Local Test Suitor",
                    email=None,
                    age=25,
                    gender="unspecified",
                    orientation="unspecified",
                    intro_message="Local development test user",
                )
            )

    if suitor.age is None or suitor.gender is None or suitor.orientation is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Please complete your profile before starting an interview "
                "(age, gender, orientation required)."
            ),
        )

    heart = await heart_repo.find_by_slug(payload.heart_slug)
    if not heart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Heart link not found"
        )
    if not heart.is_active:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Interviews are currently paused. Please check back later.",
        )
    active = await session_repo.find_active_by_suitor(suitor.id)
    if active:
        if not active.livekit_room_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have an active session that is missing room details.",
            )
        livekit_token = livekit.generate_suitor_token(
            room_name=active.livekit_room_name,
            suitor_id=str(suitor.id),
            suitor_name=suitor.name or "Suitor",
        )
        return SessionStartResponse(
            session_id=str(active.id),
            livekit_url=config.LIVEKIT_URL or "",
            livekit_token=livekit_token,
            room_name=active.livekit_room_name,
            status="reconnecting",
            message="You have an active session. Reconnecting...",
        )

    today_count = await session_repo.count_today_by_suitor(suitor.id)
    if today_count >= config.MAX_SESSIONS_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"You've reached the daily limit of {config.MAX_SESSIONS_PER_DAY} "
                "interviews. Try again tomorrow!"
            ),
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
            max_participants=2,
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
    except (RuntimeError, TwirpError) as exc:
        logger.exception("Failed to initialize LiveKit room for session %s", created.id)
        await session_repo.update_status(created.id, SessionStatus.FAILED)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to initialize LiveKit room",
        ) from exc
    finally:
        await livekit.close()

    return SessionStartResponse(
        session_id=str(created.id),
        livekit_url=config.LIVEKIT_URL or "",
        livekit_token=livekit_token,
        room_name=room_name,
        status="ready",
        message="Session created. Connect to start your interview!",
    )


@router.get("/{id}/status", response_model=SessionStatusResponse)
@inject
async def get_session_status(
    request: Request,
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

    duration_seconds: int | None = None
    if session.started_at:
        end_ref = session.ended_at or datetime.now(timezone.utc)
        duration_seconds = int(max(0.0, (end_ref - session.started_at).total_seconds()))

    turns_payload = session.turn_summaries or {}
    turns = turns_payload.get("turns", []) if isinstance(turns_payload, dict) else []
    questions_asked = len(turns) if turns else None

    heart_config = getattr(request.app.state, "heart_config", None)
    questions_total: int | None = None
    if heart_config and getattr(heart_config, "screening_questions", None) is not None:
        questions_total = len(heart_config.screening_questions)

    status_value = session.status.value
    has_verdict = score is not None
    verdict_status: str | None = None
    if has_verdict:
        verdict_status = "ready"
        status_value = "scored"
    elif session.status in {SessionStatus.COMPLETED, SessionStatus.SCORING}:
        verdict_status = "scoring"
        status_value = "scoring"
    elif session.status == SessionStatus.SCORED:
        verdict_status = "ready"
        status_value = "scored"
    elif session.status == SessionStatus.EXPIRED:
        verdict_status = "pending"

    return SessionStatusResponse(
        session_id=str(session.id),
        status=status_value,
        started_at=session.started_at,
        ended_at=session.ended_at,
        end_reason=session.end_reason,
        duration_seconds=duration_seconds,
        questions_asked=questions_asked,
        questions_total=questions_total,
        has_verdict=has_verdict,
        verdict_status=verdict_status,
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


@router.get("/pre-check", response_model=PreCheckResponse)
@inject
async def pre_check(
    request: Request,
    suitor: CurrentSuitor,
    heart_repo: HeartRepoDep,
    session_repo: SessionRepoDep,
):
    """Check whether a suitor can start a new interview session."""
    heart_id = getattr(request.app.state, "heart_id", None)
    heart = None
    if heart_id:
        try:
            heart = await heart_repo.read_by_id(heart_id)
        except NotFoundError:
            heart = None
    profile_complete = bool(suitor.age is not None and suitor.gender is not None)
    heart_active = bool(heart and heart.is_active)
    active_session = await session_repo.find_active_by_suitor(suitor.id)

    today_count = await session_repo.count_today_by_suitor(suitor.id)
    remaining = max(0, config.MAX_SESSIONS_PER_DAY - today_count)

    can_start = True
    reason: str | None = None
    if not profile_complete:
        can_start = False
        reason = "Please complete your profile first."
    elif not heart_active:
        can_start = False
        reason = "Interviews are currently paused."
    elif active_session:
        can_start = False
        reason = "You have an active interview session."
    elif remaining <= 0:
        can_start = False
        reason = f"You've reached the daily limit of {config.MAX_SESSIONS_PER_DAY} interviews."

    return PreCheckResponse(
        can_start=can_start,
        reason=reason,
        profile_complete=profile_complete,
        heart_active=heart_active,
        remaining_today=remaining,
        active_session_id=str(active_session.id) if active_session else None,
    )


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
        session_id=str(session.id),
        verdict=score.verdict,
        weighted_total=score.weighted_total,
        effort_score=score.effort_score,
        creativity_score=score.creativity_score,
        intent_clarity_score=score.intent_clarity_score,
        emotional_intelligence_score=score.emotional_intelligence_score,
        emotion_modifiers=score.emotion_modifiers,
        feedback_text=score.feedback_text,
    )
