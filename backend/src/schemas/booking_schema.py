"""Schemas for booking APIs."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class BookingSlotItem(BaseModel):
    """Available booking slot."""

    slot_id: str
    starts_at: datetime
    ends_at: datetime
    timezone: str


class BookingSlotsResponse(BaseModel):
    """List of open booking slots."""

    slots: list[BookingSlotItem]


class CreateBookingRequest(BaseModel):
    """Create booking payload."""

    session_id: uuid.UUID
    slot_id: str


class CreateBookingResponse(BaseModel):
    """Created booking payload."""

    booking_id: uuid.UUID
    session_id: uuid.UUID
    heart_id: uuid.UUID
    suitor_id: uuid.UUID
    calcom_booking_id: str
    scheduled_at: datetime
    status: str
    created_at: datetime
