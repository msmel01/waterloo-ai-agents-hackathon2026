"""Schemas for booking APIs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.models.domain_enums import BookingStatus


class AvailableSlot(BaseModel):
    """Available booking slot."""

    model_config = ConfigDict(from_attributes=True)

    slot_id: str = Field(description="Provider slot identifier.")
    starts_at: datetime = Field(description="Slot start datetime in ISO 8601.")
    ends_at: datetime = Field(description="Slot end datetime in ISO 8601.")
    timezone: str = Field(description="Timezone for this slot.")


class AvailableSlotsResponse(BaseModel):
    """List of open booking slots."""

    model_config = ConfigDict(from_attributes=True)

    slots: list[AvailableSlot] = Field(
        default_factory=list, description="Available booking slots."
    )


class BookingCreateRequest(BaseModel):
    """Create booking payload."""

    session_id: uuid.UUID = Field(
        description="Session UUID being converted to a date booking."
    )
    slot_datetime: datetime = Field(description="Selected slot datetime in ISO 8601.")


class BookingConfirmationResponse(BaseModel):
    """Created booking payload."""

    model_config = ConfigDict(from_attributes=True)

    booking_id: uuid.UUID = Field(description="Booking UUID.")
    session_id: uuid.UUID = Field(description="Related session UUID.")
    heart_id: uuid.UUID = Field(description="Heart UUID.")
    suitor_id: uuid.UUID = Field(description="Suitor UUID.")
    calcom_booking_id: str = Field(description="External calendar provider booking ID.")
    scheduled_at: datetime = Field(description="Scheduled date-time for the booking.")
    status: BookingStatus = Field(description="Booking lifecycle state.")
    created_at: datetime = Field(description="Booking creation timestamp.")


# Backward-compatible aliases
BookingSlotItem = AvailableSlot
BookingSlotsResponse = AvailableSlotsResponse
CreateBookingRequest = BookingCreateRequest
CreateBookingResponse = BookingConfirmationResponse
