"""Public profile endpoints."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from src.core.container import Container
from src.repository.heart_repository import HeartRepository
from src.repository.screening_question_repository import ScreeningQuestionRepository
from src.schemas.public_schema import PublicHeartProfileResponse

router = APIRouter(tags=["public"])

HeartRepoDep = Annotated[HeartRepository, Depends(Provide[Container.heart_repository])]
QuestionRepoDep = Annotated[
    ScreeningQuestionRepository,
    Depends(Provide[Container.screening_question_repository]),
]


@router.get("/public/{slug}", response_model=PublicHeartProfileResponse)
@inject
async def get_public_profile(
    slug: str, heart_repo: HeartRepoDep, question_repo: QuestionRepoDep
):
    """Fetch public-facing heart profile by shareable slug."""
    heart = await heart_repo.find_by_slug(slug)
    if not heart or not heart.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Public profile not found"
        )

    questions = await question_repo.find_by_heart_id(heart.id)
    return PublicHeartProfileResponse(
        display_name=heart.display_name,
        bio=heart.bio,
        photo_url=heart.photo_url,
        persona=heart.persona,
        expectations=heart.expectations,
        screening_questions=[q.question_text for q in questions],
    )
