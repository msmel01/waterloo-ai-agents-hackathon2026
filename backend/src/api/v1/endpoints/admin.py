"""Admin endpoints for static Heart operations."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from arq import create_pool
from arq.connections import RedisSettings
from dependency_injector.wiring import Provide
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import config
from src.core.container import Container
from src.core.exceptions import NotFoundError
from src.dependencies import (
    get_calcom_service,
    get_db_session,
    get_heart_id,
    get_tavus_service,
    verify_admin_key,
)
from src.repository.heart_repository import HeartRepository
from src.schemas.admin_schema import (
    AvatarCreateResponse,
    CalcomStatusInfo,
    CalendarStatusResponse,
    LinkToggleRequest,
    SystemHealthResponse,
    TavusStatusInfo,
)
from src.schemas.common_schema import SuccessResponse
from src.services.calcom_service import CalcomService
from src.services.tavus_service import TavusService

router = APIRouter(prefix="/admin", tags=["Admin"])

AdminKey = Annotated[str, Depends(verify_admin_key)]
HeartRepoDep = Annotated[HeartRepository, Depends(Provide[Container.heart_repository])]
HeartIdDep = Annotated[uuid.UUID, Depends(get_heart_id)]
TavusDep = Annotated[TavusService, Depends(get_tavus_service)]
CalcomDep = Annotated[CalcomService, Depends(get_calcom_service)]
DbDep = Annotated[AsyncSession, Depends(get_db_session)]


async def _get_heart_or_404(
    heart_repo: HeartRepository, heart_id: uuid.UUID
):  # pragma: no cover - trivial guard
    try:
        return await heart_repo.read_by_id(heart_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Heart not found"
        ) from exc


def _map_tavus_status(raw_status: str | None) -> str:
    mapping = {
        "training": "processing",
        "processing": "processing",
        "ready": "ready",
        "error": "failed",
        "failed": "failed",
    }
    return mapping.get((raw_status or "").lower(), "processing")


@router.post("/avatar/create", response_model=AvatarCreateResponse)
async def create_avatar(
    _admin: AdminKey,
    heart_repo: HeartRepoDep,
    heart_id: HeartIdDep,
    tavus: TavusDep,
):
    """Trigger Tavus replica creation from the configured Heart video URL."""
    heart = await _get_heart_or_404(heart_repo, heart_id)

    if heart.tavus_avatar_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Replica already exists: {heart.tavus_avatar_id}",
        )
    if not heart.video_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No video_url configured for the Heart profile.",
        )

    try:
        result = await tavus.create_replica(
            replica_name=f"{heart.display_name}'s Avatar",
            train_video_url=heart.video_url,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Tavus API error: {exc}",
        ) from exc

    replica_id = result.get("replica_id") or result.get("id")
    if not replica_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Tavus response missing replica_id",
        )

    await heart_repo.update_attr(heart.id, "tavus_avatar_id", str(replica_id))

    redis_pool = None
    try:
        redis_pool = await create_pool(RedisSettings.from_dsn(config.REDIS_URL))
        await redis_pool.enqueue_job(
            "poll_tavus_replica_status", str(heart.id), str(replica_id)
        )
    except Exception:
        # Do not fail setup when queue is temporarily unavailable.
        pass
    finally:
        if redis_pool is not None:
            await redis_pool.aclose()

    return AvatarCreateResponse(
        replica_id=str(replica_id),
        status="processing",
        message="Replica creation started. Poll GET /api/v1/admin/avatar/status.",
    )


@router.get("/avatar/status", response_model=TavusStatusInfo)
async def avatar_status(
    _admin: AdminKey,
    heart_repo: HeartRepoDep,
    heart_id: HeartIdDep,
    tavus: TavusDep,
):
    """Check the current Tavus replica status for the static Heart profile."""
    heart = await _get_heart_or_404(heart_repo, heart_id)
    if not heart.tavus_avatar_id:
        return TavusStatusInfo(status="not_started", replica_id=None)

    try:
        payload = await tavus.get_replica(heart.tavus_avatar_id)
        return TavusStatusInfo(
            status=_map_tavus_status(payload.get("status")),
            replica_id=heart.tavus_avatar_id,
        )
    except Exception:
        return TavusStatusInfo(status="failed", replica_id=heart.tavus_avatar_id)


@router.get("/calendar/status", response_model=CalendarStatusResponse)
async def calendar_status(
    _admin: AdminKey,
    heart_repo: HeartRepoDep,
    heart_id: HeartIdDep,
    calcom: CalcomDep,
):
    """Check cal.com integration health and return a short slot preview."""
    heart = await _get_heart_or_404(heart_repo, heart_id)
    if not heart.calcom_event_type_id:
        return CalendarStatusResponse(
            status="not_configured",
            event_type_id=None,
            slot_preview=[],
        )

    if not await calcom.validate_connection():
        return CalendarStatusResponse(
            status="error",
            event_type_id=heart.calcom_event_type_id,
            slot_preview=[],
        )

    now = datetime.now(timezone.utc)
    start = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    end = (
        (now + timedelta(days=7))
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    slot_payload = await calcom.get_available_slots(start, end)

    preview: list[str] = []
    for slot in slot_payload:
        if len(preview) >= 5:
            break
        if isinstance(slot, str):
            preview.append(slot)
            continue
        if isinstance(slot, dict):
            value = slot.get("time") or slot.get("start") or slot.get("startTime")
            if value:
                preview.append(str(value))

    return CalendarStatusResponse(
        status="connected",
        event_type_id=heart.calcom_event_type_id,
        slot_preview=preview,
    )


@router.post("/link/toggle", response_model=SuccessResponse)
async def toggle_link(
    payload: LinkToggleRequest,
    _admin: AdminKey,
    heart_repo: HeartRepoDep,
    heart_id: HeartIdDep,
):
    """Activate or deactivate the static Heart's public link."""
    await heart_repo.update_attr(heart_id, "is_active", payload.is_active)
    return SuccessResponse(
        message=f"Heart link set to {'active' if payload.is_active else 'inactive'}."
    )


@router.get("/health", response_model=SystemHealthResponse)
async def health(
    _admin: AdminKey,
    heart_repo: HeartRepoDep,
    heart_id: HeartIdDep,
    tavus: TavusDep,
    calcom: CalcomDep,
    db: DbDep,
):
    """Return overall system health for DB, Redis, Tavus, cal.com, and Heart config."""
    heart = await _get_heart_or_404(heart_repo, heart_id)

    db_status = "connected"
    redis_status = "connected"

    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    redis_pool = None
    try:
        redis_pool = await create_pool(RedisSettings.from_dsn(config.REDIS_URL))
        await redis_pool.ping()
    except Exception:
        redis_status = "error"
    finally:
        if redis_pool is not None:
            await redis_pool.aclose()

    if heart.tavus_avatar_id:
        try:
            payload = await tavus.get_replica(heart.tavus_avatar_id)
            tavus_info = TavusStatusInfo(
                status=_map_tavus_status(payload.get("status")),
                replica_id=heart.tavus_avatar_id,
            )
        except Exception:
            tavus_info = TavusStatusInfo(
                status="failed",
                replica_id=heart.tavus_avatar_id,
            )
    else:
        tavus_info = TavusStatusInfo(status="not_started", replica_id=None)

    calcom_status = "not_configured"
    if heart.calcom_event_type_id:
        try:
            calcom_status = (
                "connected" if await calcom.validate_connection() else "error"
            )
        except Exception:
            calcom_status = "error"
    calcom_info = CalcomStatusInfo(
        status=calcom_status,
        event_type_id=heart.calcom_event_type_id,
    )

    overall = "healthy"
    if db_status == "error":
        overall = "unhealthy"
    elif redis_status == "error" or calcom_status == "error":
        overall = "degraded"
    elif tavus_info.status in {"failed", "not_started"}:
        overall = "degraded"

    return SystemHealthResponse(
        status=overall,
        heart_loaded=True,
        heart_name=heart.display_name,
        heart_slug=heart.shareable_slug,
        database=db_status,
        redis=redis_status,
        tavus=tavus_info,
        calcom=calcom_info,
    )
