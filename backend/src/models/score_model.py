"""Score model."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlmodel import Field, SQLModel

from src.models.domain_enums import Verdict


class ScoreDb(SQLModel, table=True):
    """Final scoring artifact for a session."""

    __tablename__ = "scores"

    id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    session_id: uuid.UUID = Field(
        sa_column=Column(
            UUID(as_uuid=True),
            ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        )
    )
    effort_score: float = Field(sa_column=Column(Float, nullable=False))
    creativity_score: float = Field(sa_column=Column(Float, nullable=False))
    intent_clarity_score: float = Field(sa_column=Column(Float, nullable=False))
    emotional_intelligence_score: float = Field(sa_column=Column(Float, nullable=False))
    weighted_total: float = Field(sa_column=Column(Float, nullable=False, index=True))
    emotion_modifiers: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )
    verdict: Verdict = Field(
        sa_column=Column(SAEnum(Verdict, name="verdict"), nullable=False, index=True)
    )
    feedback_text: str = Field(sa_column=Column(Text, nullable=False))
    raw_llm_response: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        )
    )
