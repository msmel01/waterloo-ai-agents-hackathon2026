"""Shared FastAPI dependencies for auth and guard checks."""

from typing import TYPE_CHECKING, Annotated

import redis.asyncio as redis
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from src.core.config import config
from src.core.container import Container
from src.core.security import get_current_user
from src.models.suitor_model import SuitorDb
from src.repository.suitor_repository import SuitorRepository
from src.services.calcom_service import CalcomService
from src.services.tavus_service import TavusService

if TYPE_CHECKING:
    from src.services.config_loader import HeartConfig

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


async def get_db_session(request: Request):
    """Yield an async database session from the app container."""
    database = request.app.state.container.database()
    async with database.session() as session:
        yield session


def get_tavus_service(request: Request) -> TavusService:
    """Build Tavus client from loaded heart config."""
    heart_config = get_heart_config(request)
    return TavusService(heart_config.avatar.tavus_api_key)


def get_calcom_service(request: Request) -> CalcomService:
    """Build cal.com client from loaded heart config."""
    heart_config = get_heart_config(request)
    return CalcomService(
        heart_config.calendar.calcom_api_key,
        heart_config.calendar.calcom_event_type_id,
    )


def get_heart_id(request: Request):
    """Return seeded static heart UUID from app state."""
    heart_id = getattr(request.app.state, "heart_id", None)
    if not heart_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Heart profile is not initialized",
        )
    return heart_id


def get_heart_config(request: Request) -> "HeartConfig":
    """Return loaded static heart config from app state."""
    heart_config = getattr(request.app.state, "heart_config", None)
    if not heart_config:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Heart config is not loaded",
        )
    return heart_config


def get_redis_client():
    """Create a Redis client for runtime health checks and background queues."""
    return redis.from_url(config.REDIS_URL)
