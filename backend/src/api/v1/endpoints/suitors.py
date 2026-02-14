"""Suitor endpoints."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from src.core.container import Container
from src.dependencies import get_current_suitor
from src.models.suitor_model import SuitorDb
from src.repository.suitor_repository import SuitorRepository
from src.schemas.suitor_schema import SuitorProfileResponse, SuitorRegisterRequest

router = APIRouter(prefix="/suitors", tags=["Suitors"])

CurrentSuitor = Annotated[SuitorDb, Depends(get_current_suitor)]
SuitorRepoDep = Annotated[
    SuitorRepository, Depends(Provide[Container.suitor_repository])
]


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
            "age": payload.age,
            "gender": payload.gender,
            "orientation": payload.orientation,
            "intro_message": payload.intro_message,
        },
    )
    if not updated:
        updated = suitor

    return SuitorProfileResponse(
        id=updated.id,
        name=updated.name,
        email=updated.email,
        age=updated.age,
        gender=updated.gender,
        orientation=updated.orientation,
        intro_message=updated.intro_message,
        is_profile_complete=bool(
            updated.age and updated.gender and updated.orientation
        ),
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )
