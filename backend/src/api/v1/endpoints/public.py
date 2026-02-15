"""Public profile endpoints."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.core.config import config
from src.core.container import Container
from src.repository.heart_repository import HeartRepository
from src.repository.screening_question_repository import ScreeningQuestionRepository
from src.schemas.public_schema import PublicHeartProfileResponse

router = APIRouter(tags=["Public"])

HeartRepoDep = Annotated[HeartRepository, Depends(Provide[Container.heart_repository])]
QuestionRepoDep = Annotated[
    ScreeningQuestionRepository,
    Depends(Provide[Container.screening_question_repository]),
]


@router.get("/public/{slug}", response_model=PublicHeartProfileResponse)
@inject
async def get_public_profile(
    slug: str,
    request: Request,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """Get the Heart public profile for the suitor landing page."""
    heart = await heart_repo.find_by_slug(slug)
    if not heart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Public profile not found"
        )

    questions = await question_repo.find_by_heart_id(heart.id)
    heart_config = getattr(request.app.state, "heart_config", None)
    has_calendar = bool(heart.calcom_event_type_id)
    if heart_config:
        has_calendar = bool(heart_config.calendar.calcom_event_type_id)

    agent_ready = await _is_agent_ready()
    is_accepting = bool(heart.is_active and agent_ready)
    question_count = len(questions)
    pause_message = (
        "Screening is currently paused. Please check back later."
        if not heart.is_active
        else None
    )

    return PublicHeartProfileResponse(
        display_name=heart.display_name,
        bio=heart.bio,
        photo_url=heart.photo_url,
        agent_ready=agent_ready,
        has_calendar=has_calendar,
        question_count=question_count,
        estimated_duration=_estimate_duration(question_count),
        persona_preview=_build_persona_preview(heart.persona),
        is_accepting=is_accepting,
        active=bool(heart.is_active),
        message=pause_message,
    )


def _build_persona_preview(persona: dict | None) -> str | None:
    """Build short persona teaser from top traits."""
    if not persona:
        return None
    traits = persona.get("traits", [])[:3]
    if not traits:
        return None
    if len(traits) == 1:
        return traits[0]
    return f"{', '.join(traits[:-1])}, and {traits[-1]}"


def _estimate_duration(question_count: int) -> str:
    """Rough estimate: ~1-2 minutes per question."""
    low = max(1, question_count)
    high = max(2, question_count * 2)
    return f"{low}-{high} minutes"


async def _is_agent_ready() -> bool:
    """MVP readiness check for agent availability."""
    _ = config
    return True
