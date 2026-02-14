"""Session model."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, SQLModel

from src.models.domain_enums import SessionStatus


class SessionDb(SQLModel, table=True):
    """Interview session between a heart and suitor."""

    __tablename__ = "sessions"

    id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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
    livekit_room_name: Optional[str] = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    status: SessionStatus = Field(
        default=SessionStatus.PENDING,
        sa_column=Column(
            SAEnum(SessionStatus, name="session_status"),
            nullable=False,
            server_default=SessionStatus.PENDING.value,
            index=True,
        ),
    )
    started_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    ended_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        )
    )
