"""Admin endpoints for static-Heart MVP operations."""

from __future__ import annotations

import uuid
from typing import Annotated

import redis.asyncio as redis
from dependency_injector.wiring import Provide
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from src.core.config import config
from src.core.container import Container
from src.dependencies import verify_admin_key
from src.repository.conversation_turn_repository import ConversationTurnRepository
from src.repository.heart_repository import HeartRepository
from src.repository.score_repository import ScoreRepository
from src.repository.session_repository import SessionRepository
from src.schemas.admin_schema import (
    AvatarCreateResponse,
    CalcomStatusInfo,
    CalendarStatusResponse,
    LinkToggleRequest,
    SystemHealthResponse,
    TavusStatusInfo,
)
from src.schemas.common_schema import SuccessResponse
from src.schemas.heart_schema import (
    DashboardStatsResponse,
    SessionDetailResponse,
    SessionDetailScore,
    SessionDetailTurn,
    SessionListResponse,
    SessionSummaryItem,
)

router = APIRouter(prefix="/admin", tags=["Admin"])

AdminKey = Annotated[str, Depends(verify_admin_key)]
HeartRepoDep = Annotated[HeartRepository, Depends(Provide[Container.heart_repository])]
SessionRepoDep = Annotated[
    SessionRepository, Depends(Provide[Container.session_repository])
]
TurnRepoDep = Annotated[
    ConversationTurnRepository, Depends(Provide[Container.conversation_turn_repository])
]
ScoreRepoDep = Annotated[ScoreRepository, Depends(Provide[Container.score_repository])]


async def _get_primary_heart_or_404(heart_repo: HeartRepository):
    heart = await heart_repo.get_primary_heart()
    if not heart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Heart not found"
        )
    return heart


@router.post("/avatar/create", response_model=AvatarCreateResponse)
async def create_avatar(_admin: AdminKey, heart_repo: HeartRepoDep):
    """Trigger Tavus avatar creation (placeholder stub for static Heart MVP)."""
    heart = await _get_primary_heart_or_404(heart_repo)

    if heart.tavus_avatar_id:
        return AvatarCreateResponse(
            replica_id=heart.tavus_avatar_id,
            status="ready",
            message="Avatar replica already exists.",
        )

    replica_id = f"r_{uuid.uuid4().hex[:12]}"
    heart.tavus_avatar_id = replica_id
    await heart_repo.update(heart.id, heart)

    return AvatarCreateResponse(
        replica_id=replica_id,
        status="processing",
        message="Avatar creation triggered. Poll status endpoint for updates.",
    )


@router.get("/avatar/status", response_model=TavusStatusInfo)
async def avatar_status(_admin: AdminKey, heart_repo: HeartRepoDep):
    """Return Tavus avatar status for the static Heart profile."""
    heart = await _get_primary_heart_or_404(heart_repo)
    if not heart.tavus_avatar_id:
        return TavusStatusInfo(status="not_started", replica_id=None)
    return TavusStatusInfo(status="ready", replica_id=heart.tavus_avatar_id)


@router.get("/calendar/status", response_model=CalendarStatusResponse)
async def calendar_status(_admin: AdminKey, heart_repo: HeartRepoDep):
    """Return cal.com configuration health and slot preview (placeholder)."""
    heart = await _get_primary_heart_or_404(heart_repo)

    if not config.CALCOM_API_KEY or not heart.calcom_event_type_id:
        return CalendarStatusResponse(
            status="not_configured",
            event_type_id=heart.calcom_event_type_id,
            slot_preview=[],
        )

    return CalendarStatusResponse(
        status="connected",
        event_type_id=heart.calcom_event_type_id,
        slot_preview=["2026-02-15T18:00:00Z", "2026-02-16T19:00:00Z"],
    )


@router.post("/link/toggle", response_model=SuccessResponse)
async def toggle_link(
    payload: LinkToggleRequest, _admin: AdminKey, heart_repo: HeartRepoDep
):
    """Activate or deactivate the static Heart's public link."""
    heart = await _get_primary_heart_or_404(heart_repo)
    heart.is_active = payload.is_active
    await heart_repo.update(heart.id, heart)
    return SuccessResponse(
        message=f"Heart link set to {'active' if payload.is_active else 'inactive'}."
    )


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def dashboard_stats(
    _admin: AdminKey,
    heart_repo: HeartRepoDep,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
):
    """Get admin dashboard statistics for the static Heart profile."""
    heart = await _get_primary_heart_or_404(heart_repo)
    sessions = await session_repo.find_by_heart_id(heart.id)
    completed_sessions = [s for s in sessions if s.status.value == "completed"]

    scores = []
    for s in sessions:
        score = await score_repo.find_by_session_id(s.id)
        if score:
            scores.append(score)

    date_verdicts = sum(1 for score in scores if score.verdict.value == "date")
    match_rate = float((date_verdicts / len(scores)) * 100) if scores else 0.0
    avg_weighted = (
        sum(score.weighted_total for score in scores) / len(scores) if scores else 0.0
    )

    return DashboardStatsResponse(
        total_suitors=len(sessions),
        match_rate=match_rate,
        avg_scores=avg_weighted,
        total_sessions=len(sessions),
        completed_sessions=len(completed_sessions),
        upcoming_bookings=0,
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    _admin: AdminKey,
    heart_repo: HeartRepoDep,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
):
    """List all sessions for admin moderation and review."""
    heart = await _get_primary_heart_or_404(heart_repo)
    sessions = await session_repo.find_by_heart_id(heart.id)

    items: list[SessionSummaryItem] = []
    for session in sessions:
        score = await score_repo.find_by_session_id(session.id)
        items.append(
            SessionSummaryItem(
                id=session.id,
                suitor_id=session.suitor_id,
                suitor_name="Suitor",
                status=session.status,
                created_at=session.created_at,
                weighted_total=score.weighted_total if score else None,
                verdict=score.verdict if score else None,
            )
        )

    return SessionListResponse(
        items=items, total=len(items), page=1, per_page=max(len(items), 1)
    )


@router.get("/sessions/{id}", response_model=SessionDetailResponse)
async def session_detail(
    id: uuid.UUID,
    _admin: AdminKey,
    session_repo: SessionRepoDep,
    turn_repo: TurnRepoDep,
    score_repo: ScoreRepoDep,
):
    """Get full transcript and score detail for one session."""
    session = await session_repo.read_by_id(id)
    turns = await turn_repo.find_by_session_id(session.id)
    score = await score_repo.find_by_session_id(session.id)

    return SessionDetailResponse(
        session_id=session.id,
        heart_id=session.heart_id,
        suitor_id=session.suitor_id,
        suitor_name="Suitor",
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        created_at=session.created_at,
        turns=[
            SessionDetailTurn(
                id=turn.id,
                turn_index=turn.turn_index,
                speaker=turn.speaker,
                content=turn.content,
                emotion_data=turn.emotion_data,
                duration_seconds=turn.duration_seconds,
                created_at=turn.created_at,
            )
            for turn in turns
        ],
        score=(
            SessionDetailScore(
                effort_score=score.effort_score,
                creativity_score=score.creativity_score,
                intent_clarity_score=score.intent_clarity_score,
                emotional_intelligence_score=score.emotional_intelligence_score,
                weighted_total=score.weighted_total,
                verdict=score.verdict,
                feedback_text=score.feedback_text,
                emotion_modifiers=score.emotion_modifiers,
            )
            if score
            else None
        ),
    )


@router.get("/health", response_model=SystemHealthResponse)
async def health(_admin: AdminKey, heart_repo: HeartRepoDep):
    """Return system health for database, redis, tavus, cal.com, and heart readiness."""
    db_status = "connected"
    redis_status = "connected"

    heart = await heart_repo.get_primary_heart()

    try:
        async with heart_repo.session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    try:
        redis_client = redis.from_url(config.REDIS_URL)
        await redis_client.ping()
        await redis_client.close()
    except Exception:
        redis_status = "error"

    tavus_info = TavusStatusInfo(
        status="ready" if heart and heart.tavus_avatar_id else "not_started",
        replica_id=heart.tavus_avatar_id if heart else None,
    )
    calcom_info = CalcomStatusInfo(
        status="connected"
        if heart and config.CALCOM_API_KEY and heart.calcom_event_type_id
        else "not_configured",
        event_type_id=heart.calcom_event_type_id if heart else None,
    )

    overall = "healthy"
    if db_status == "error" or redis_status == "error":
        overall = "unhealthy"
    elif tavus_info.status != "ready" or calcom_info.status != "connected":
        overall = "degraded"

    return SystemHealthResponse(
        status=overall,
        heart_loaded=heart is not None,
        heart_name=heart.display_name if heart else None,
        heart_slug=heart.shareable_slug if heart else None,
        database=db_status,
        redis=redis_status,
        tavus=tavus_info,
        calcom=calcom_info,
    )
