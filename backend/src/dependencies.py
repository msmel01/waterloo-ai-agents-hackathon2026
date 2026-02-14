"""Shared FastAPI dependencies for auth and guard checks."""

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from src.core.config import config
from src.core.container import Container
from src.core.security import get_current_user
from src.models.suitor_model import SuitorDb
from src.repository.suitor_repository import SuitorRepository

admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


async def verify_admin_key(api_key: str | None = Security(admin_key_header)) -> str:
    """Simple API key auth for admin endpoints."""
    expected = config.ADMIN_API_KEY
    if not api_key or not expected or api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin API key",
        )
    return api_key


@inject
async def get_current_suitor(
    clerk_user_id: Annotated[str, Depends(get_current_user)],
    suitor_repo: SuitorRepository = Depends(Provide[Container.suitor_repository]),
) -> SuitorDb:
    """Resolve authenticated Clerk user to a Suitor profile."""
    suitor = await suitor_repo.find_by_clerk_id(clerk_user_id)
    if not suitor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Suitor profile not found. Please complete registration.",
        )

    return suitor
