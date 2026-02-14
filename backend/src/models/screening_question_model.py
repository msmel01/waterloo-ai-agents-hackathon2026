"""Screening question model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, SQLModel


class ScreeningQuestionDb(SQLModel, table=True):
    """Custom screening questions for a heart profile."""

    __tablename__ = "screening_questions"

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
    question_text: str = Field(sa_column=Column(Text, nullable=False))
    order_index: int = Field(sa_column=Column(Integer, nullable=False, index=True))
    is_required: bool = Field(
        default=True, sa_column=Column(Boolean, nullable=False, server_default="true")
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        )
    )
