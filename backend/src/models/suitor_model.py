"""Suitor model."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, SQLModel


class SuitorDb(SQLModel, table=True):
    """Suitor information collected before interview."""

    __tablename__ = "suitors"

    id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    clerk_user_id: Optional[str] = Field(
        default=None,
        sa_column=Column(String(255), nullable=True, unique=True, index=True),
    )
    name: str = Field(sa_column=Column(String(255), nullable=False))
    email: Optional[str] = Field(
        default=None,
        sa_column=Column(String(320), nullable=True, index=True),
    )
    age: Optional[int] = Field(default=None, sa_column=Column(Integer, nullable=True))
    gender: Optional[str] = Field(
        default=None, sa_column=Column(String(50), nullable=True)
    )
    orientation: Optional[str] = Field(
        default=None, sa_column=Column(String(50), nullable=True)
    )
    intro_message: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
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
