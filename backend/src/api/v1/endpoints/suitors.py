"""Suitor endpoints."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from src.core.container import Container
from src.repository.suitor_repository import SuitorRepository
from src.schemas.suitor_schema import SuitorRegisterRequest, SuitorRegisterResponse

router = APIRouter(prefix="/suitors", tags=["Suitors"])

SuitorRepoDep = Annotated[
    SuitorRepository, Depends(Provide[Container.suitor_repository])
]


@router.post(
    "/register",
    response_model=SuitorRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def register_suitor(payload: SuitorRegisterRequest, suitor_repo: SuitorRepoDep):
    """Register a suitor before starting the interview flow."""
    suitor = await suitor_repo.create(
        suitor_repo.model(
            name=payload.name,
            email=payload.email,
            intro_message=payload.intro_message,
        )
    )
    return SuitorRegisterResponse(suitor_id=suitor.id, created_at=suitor.created_at)
