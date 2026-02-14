"""Conversation turn model."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlmodel import Field, SQLModel

from src.models.domain_enums import ConversationSpeaker


class ConversationTurnDb(SQLModel, table=True):
    """Transcript turn recorded for a session."""

    __tablename__ = "conversation_turns"

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
    turn_index: int = Field(sa_column=Column(Integer, nullable=False, index=True))
    speaker: ConversationSpeaker = Field(
        sa_column=Column(
            SAEnum(ConversationSpeaker, name="conversation_speaker"),
            nullable=False,
            index=True,
        )
    )
    content: str = Field(sa_column=Column(Text, nullable=False))
    emotion_data: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    duration_seconds: Optional[float] = Field(
        default=None, sa_column=Column(Float, nullable=True)
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        )
    )
