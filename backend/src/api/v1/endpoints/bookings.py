"""Booking endpoints."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from src.core.container import Container
from src.dependencies import get_current_suitor
from src.models.domain_enums import BookingStatus
from src.models.suitor_model import SuitorDb
from src.repository.booking_repository import BookingRepository
from src.repository.session_repository import SessionRepository
from src.schemas.booking_schema import (
    AvailableSlot,
    AvailableSlotsResponse,
    BookingConfirmationResponse,
    BookingCreateRequest,
)

router = APIRouter(prefix="/bookings", tags=["Bookings"])

CurrentSuitor = Annotated[SuitorDb, Depends(get_current_suitor)]
BookingRepoDep = Annotated[
    BookingRepository, Depends(Provide[Container.booking_repository])
]
SessionRepoDep = Annotated[
    SessionRepository, Depends(Provide[Container.session_repository])
]


@router.get("/slots", response_model=AvailableSlotsResponse)
async def get_slots(_suitor: CurrentSuitor):
    """Get available date booking slots for authenticated suitors (placeholder)."""
    now = datetime.now(timezone.utc)
    slots = [
        AvailableSlot(
            slot_id=f"slot-{index + 1}",
            starts_at=now + timedelta(days=1, hours=index),
            ends_at=now + timedelta(days=1, hours=index + 1),
            timezone="UTC",
        )
        for index in range(3)
    ]
    return AvailableSlotsResponse(slots=slots)


@router.post(
    "/create",
    response_model=BookingConfirmationResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_booking(
    payload: BookingCreateRequest,
    suitor: CurrentSuitor,
    booking_repo: BookingRepoDep,
    session_repo: SessionRepoDep,
):
    """Create a booking confirmation for an authenticated suitor's session."""
    session = await session_repo.read_by_id(payload.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.suitor_id != suitor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    created = await booking_repo.create(
        booking_repo.model(
            session_id=session.id,
            heart_id=session.heart_id,
            suitor_id=session.suitor_id,
            calcom_booking_id=f"cal_{uuid.uuid4().hex[:16]}",
            scheduled_at=payload.slot_datetime,
            status=BookingStatus.CONFIRMED,
        )
    )

    return BookingConfirmationResponse(
        booking_id=created.id,
        session_id=created.session_id,
        heart_id=created.heart_id,
        suitor_id=created.suitor_id,
        calcom_booking_id=created.calcom_booking_id,
        scheduled_at=created.scheduled_at,
        status=created.status,
        created_at=created.created_at,
    )
