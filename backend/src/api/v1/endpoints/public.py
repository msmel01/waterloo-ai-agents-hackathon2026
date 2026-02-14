"""Public profile endpoints."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request, status

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
    if not heart.is_active:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This link is currently inactive",
        )

    questions = await question_repo.find_by_heart_id(heart.id)
    heart_config = getattr(request.app.state, "heart_config", None)
    has_calendar = bool(heart.calcom_event_type_id)
    if heart_config:
        has_calendar = bool(heart_config.calendar.calcom_event_type_id)

    return PublicHeartProfileResponse(
        display_name=heart.display_name,
        bio=heart.bio,
        photo_url=heart.photo_url,
        avatar_ready=heart.tavus_avatar_id is not None,
        has_calendar=has_calendar,
        question_count=len(questions),
        persona_preview=_build_persona_preview(heart.persona),
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
