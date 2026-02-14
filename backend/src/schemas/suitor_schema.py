"""Schemas for suitor onboarding APIs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SuitorRegisterRequest(BaseModel):
    """Suitor profile completion payload after Clerk authentication."""

    age: int = Field(ge=18, le=100, description="Suitor's age (must be 18+).")
    gender: str = Field(max_length=50, description="Suitor's gender identity.")
    orientation: str = Field(max_length=50, description="Suitor's orientation.")
    intro_message: str | None = Field(
        default=None, max_length=500, description="Optional intro message."
    )


class SuitorProfileResponse(BaseModel):
    """Suitor self-profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Suitor UUID.")
    name: str = Field(description="Suitor display name from Clerk profile.")
    email: str | None = Field(default=None, description="Suitor email.")
    age: int | None = Field(default=None, description="Suitor age.")
    gender: str | None = Field(default=None, description="Suitor gender identity.")
    orientation: str | None = Field(default=None, description="Suitor orientation.")
    intro_message: str | None = Field(
        default=None, description="Optional intro message."
    )
    is_profile_complete: bool = Field(
        description="Whether required profile fields are complete."
    )
    created_at: datetime = Field(description="Profile creation timestamp.")
    updated_at: datetime = Field(description="Profile update timestamp.")


# Backward-compatible alias
SuitorRegisterResponse = SuitorProfileResponse
