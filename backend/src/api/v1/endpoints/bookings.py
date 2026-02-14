"""Booking endpoints."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from src.core.container import Container
from src.models.domain_enums import BookingStatus
from src.repository.booking_repository import BookingRepository
from src.repository.session_repository import SessionRepository
from src.schemas.booking_schema import (
    BookingSlotItem,
    BookingSlotsResponse,
    CreateBookingRequest,
    CreateBookingResponse,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])

BookingRepoDep = Annotated[
    BookingRepository, Depends(Provide[Container.booking_repository])
]
SessionRepoDep = Annotated[
    SessionRepository, Depends(Provide[Container.session_repository])
]


@router.get("/slots", response_model=BookingSlotsResponse)
async def get_slots():
    """Return placeholder cal.com slots for local development."""
    now = datetime.now(timezone.utc)
    slots = [
        BookingSlotItem(
            slot_id=f"slot-{index + 1}",
            starts_at=now + timedelta(days=1, hours=index),
            ends_at=now + timedelta(days=1, hours=index + 1),
            timezone="UTC",
        )
        for index in range(3)
    ]
    return BookingSlotsResponse(slots=slots)


@router.post(
    "/create", response_model=CreateBookingResponse, status_code=status.HTTP_201_CREATED
)
@inject
async def create_booking(
    payload: CreateBookingRequest,
    booking_repo: BookingRepoDep,
    session_repo: SessionRepoDep,
):
    """Create a placeholder booking for a successful session."""
    session = await session_repo.read_by_id(payload.session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    created = await booking_repo.create(
        booking_repo.model(
            session_id=session.id,
            heart_id=session.heart_id,
            suitor_id=session.suitor_id,
            calcom_booking_id=f"cal_{uuid.uuid4().hex[:16]}",
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=2),
            status=BookingStatus.CONFIRMED,
        )
    )

    return CreateBookingResponse(
        booking_id=created.id,
        session_id=created.session_id,
        heart_id=created.heart_id,
        suitor_id=created.suitor_id,
        calcom_booking_id=created.calcom_booking_id,
        scheduled_at=created.scheduled_at,
        status=created.status.value,
        created_at=created.created_at,
    )
