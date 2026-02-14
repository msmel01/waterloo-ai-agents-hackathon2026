"""Schemas for suitor onboarding APIs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SuitorRegisterRequest(BaseModel):
    """Suitor registration payload."""

    name: str = Field(description="Suitor full name.")
    email: str | None = Field(
        default=None, description="Optional suitor email address."
    )
    intro_message: str | None = Field(
        default=None, description="Optional intro message before interview starts."
    )


class SuitorRegisterResponse(BaseModel):
    """Suitor registration response."""

    model_config = ConfigDict(from_attributes=True)

    suitor_id: uuid.UUID = Field(description="Newly created suitor UUID.")
    created_at: datetime = Field(description="Suitor creation timestamp.")
