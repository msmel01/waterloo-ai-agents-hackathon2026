"""Suitor model."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlmodel import Field, SQLModel


class SuitorDb(SQLModel, table=True):
    """Suitor information collected before interview."""

    __tablename__ = "suitors"

    id: uuid.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    )
    name: str = Field(sa_column=Column(String(255), nullable=False))
    email: Optional[str] = Field(
        default=None, sa_column=Column(String(320), nullable=True, index=True)
    )
    intro_message: Optional[str] = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), nullable=False, server_default=func.now()
        )
    )
