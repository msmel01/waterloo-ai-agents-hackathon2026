"""Suitor endpoints."""

from datetime import datetime, timezone
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from src.core.config import config
from src.core.container import Container
from src.dependencies import get_current_suitor
from src.models.suitor_model import SuitorDb
from src.repository.score_repository import ScoreRepository
from src.repository.session_repository import SessionRepository
from src.repository.suitor_repository import SuitorRepository
from src.schemas.session_schema import SessionSummary, SuitorSessionsResponse
from src.schemas.suitor_schema import SuitorProfileResponse, SuitorRegisterRequest

router = APIRouter(prefix="/suitors", tags=["Suitors"])

CurrentSuitor = Annotated[SuitorDb, Depends(get_current_suitor)]
SuitorRepoDep = Annotated[
    SuitorRepository, Depends(Provide[Container.suitor_repository])
]
SessionRepoDep = Annotated[
    SessionRepository, Depends(Provide[Container.session_repository])
]
ScoreRepoDep = Annotated[ScoreRepository, Depends(Provide[Container.score_repository])]


@router.post("/register", response_model=SuitorProfileResponse)
@inject
async def complete_suitor_profile(
    payload: SuitorRegisterRequest,
    suitor: CurrentSuitor,
    suitor_repo: SuitorRepoDep,
):
    """Complete authenticated suitor profile before interview starts."""
    updated = await suitor_repo.update_by_clerk_id(
        suitor.clerk_user_id or "",
        {
            "name": payload.name.strip(),
            "age": payload.age,
            "gender": payload.gender,
            "orientation": payload.orientation,
            "intro_message": payload.intro_message,
        },
    )
    if not updated:
        updated = suitor

    return SuitorProfileResponse.model_validate(updated)


@router.get("/me", response_model=SuitorProfileResponse)
async def get_my_profile(suitor: CurrentSuitor):
    """Get the authenticated suitor profile."""
    return SuitorProfileResponse.model_validate(suitor)


@router.get("/me/sessions", response_model=SuitorSessionsResponse)
@inject
async def get_my_sessions(
    suitor: CurrentSuitor,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
):
    """List authenticated suitor's recent sessions and remaining daily quota."""
    sessions = await session_repo.find_by_suitor(suitor.id, limit=20)
    today_count = await session_repo.count_today_by_suitor(suitor.id)
    daily_limit = config.MAX_SESSIONS_PER_DAY

    summaries: list[SessionSummary] = []
    for session in sessions:
        score = await score_repo.find_by_session_id(session.id)
        duration_seconds: int | None = None
        if session.started_at:
            end_ref = session.ended_at or datetime.now(timezone.utc)
            duration_seconds = int(
                max(0.0, (end_ref - session.started_at).total_seconds())
            )

        summaries.append(
            SessionSummary(
                session_id=str(session.id),
                status=session.status.value,
                started_at=session.started_at,
                ended_at=session.ended_at,
                duration_seconds=duration_seconds,
                end_reason=session.end_reason,
                has_verdict=score is not None,
                verdict=score.verdict.value if score else None,
                final_score=score.final_score if score else None,
            )
        )

    return SuitorSessionsResponse(
        sessions=summaries,
        total=len(summaries),
        daily_limit=daily_limit,
        remaining_today=max(0, daily_limit - today_count),
    )
