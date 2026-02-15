"""Score model."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
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
    emotion_modifier: float = Field(
        default=0.0, sa_column=Column(Float, nullable=False, server_default="0")
    )
    emotion_modifier_reasons: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default="[]"),
    )
    raw_score: float = Field(
        default=0.0, sa_column=Column(Float, nullable=False, server_default="0")
    )
    final_score: float = Field(
        default=0.0, sa_column=Column(Float, nullable=False, server_default="0")
    )
    verdict_threshold: float = Field(
        default=65.0, sa_column=Column(Float, nullable=False, server_default="65")
    )
    verdict: Verdict = Field(
        sa_column=Column(SAEnum(Verdict, name="verdict"), nullable=False, index=True)
    )
    feedback_text: str = Field(sa_column=Column(Text, nullable=False))
    feedback_summary: str = Field(
        default="", sa_column=Column(Text, nullable=False, server_default="")
    )
    feedback_strengths: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default="[]"),
    )
    feedback_improvements: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default="[]"),
    )
    feedback_json: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    feedback_heart_note: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    per_question_scores: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default="[]"),
    )
    claude_model: str = Field(
        default="claude-sonnet-4-20250514",
        sa_column=Column(
            String(128), nullable=False, server_default="claude-sonnet-4-20250514"
        ),
    )
    claude_input_tokens: Optional[int] = Field(
        default=None, sa_column=Column(Integer, nullable=True)
    )
    claude_output_tokens: Optional[int] = Field(
        default=None, sa_column=Column(Integer, nullable=True)
    )
    scoring_duration_ms: Optional[int] = Field(
        default=None, sa_column=Column(Integer, nullable=True)
    )
    raw_llm_response: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        )
    )
