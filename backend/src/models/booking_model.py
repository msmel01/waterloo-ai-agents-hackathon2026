"""Booking model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, SQLModel

from src.models.domain_enums import BookingStatus


class BookingDb(SQLModel, table=True):
    """Calendar booking created from a successful session."""

    __tablename__ = "bookings"

    id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    session_id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    heart_id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("hearts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    suitor_id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("suitors.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    calcom_booking_id: str = Field(
        sa_column=Column(String(255), nullable=False, index=True)
    )
    scheduled_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True)
    )
    status: BookingStatus = Field(
        default=BookingStatus.CONFIRMED,
        sa_column=Column(
            SAEnum(BookingStatus, name="booking_status"),
            nullable=False,
            server_default=BookingStatus.CONFIRMED.value,
            index=True,
        ),
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        )
    )
