"""Heart model for profile and dating preferences."""

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlmodel import Field, SQLModel


class HeartDb(SQLModel, table=True):
    """Heart account synced from Clerk."""

    __tablename__ = "hearts"

    id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    clerk_user_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String(255), unique=True, index=True, nullable=True),
    )
    email: Optional[str] = Field(
        default=None,
        sa_column=Column(String(320), unique=True, index=True, nullable=True),
    )
    display_name: str = Field(sa_column=Column(String(255), nullable=False))
    bio: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    photo_url: Optional[str] = Field(
        default=None, sa_column=Column(String(1024), nullable=True)
    )
    video_url: Optional[str] = Field(
        default=None, sa_column=Column(String(1024), nullable=True)
    )
    tavus_avatar_id: Optional[str] = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    tavus_persona_id: Optional[str] = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    persona: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )
    expectations: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )
    calcom_user_id: Optional[str] = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    calcom_event_type_id: Optional[str] = Field(
        default=None, sa_column=Column(String(255), nullable=True)
    )
    shareable_slug: str = Field(sa_column=Column(String(255), unique=True, index=True))
    is_active: bool = Field(
        default=True, sa_column=Column(Boolean, nullable=False, server_default="true")
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            server_default=func.now(),
            onupdate=func.now(),
        )
    )
