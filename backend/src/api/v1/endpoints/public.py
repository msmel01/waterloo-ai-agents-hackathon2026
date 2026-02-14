"""Public profile endpoints."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from src.core.container import Container
from src.repository.heart_repository import HeartRepository
from src.schemas.public_schema import PublicHeartProfileResponse

router = APIRouter(tags=["Public"])

HeartRepoDep = Annotated[HeartRepository, Depends(Provide[Container.heart_repository])]


@router.get("/public/{slug}", response_model=PublicHeartProfileResponse)
@inject
async def get_public_profile(slug: str, heart_repo: HeartRepoDep):
    """Get limited public profile information for a heart by slug."""
    heart = await heart_repo.find_by_slug(slug)
    if not heart or not heart.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Public profile not found"
        )

    bio_snippet = (
        (heart.bio[:140] + "...") if heart.bio and len(heart.bio) > 140 else heart.bio
    )

    return PublicHeartProfileResponse(
        display_name=heart.display_name,
        bio_snippet=bio_snippet,
        avatar_preview_url=heart.photo_url,
        shareable_slug=heart.shareable_slug,
    )
