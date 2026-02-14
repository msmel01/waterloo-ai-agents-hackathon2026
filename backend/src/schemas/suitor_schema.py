"""Schemas for suitor onboarding APIs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field


class SuitorRegisterRequest(BaseModel):
    """Suitor profile completion payload after Clerk authentication."""

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Suitor display name for the interview.",
    )
    age: int = Field(ge=18, le=100, description="Suitor's age (must be 18+).")
    gender: str = Field(
        min_length=1, max_length=50, description="Suitor's gender identity."
    )
    orientation: str = Field(
        min_length=1, max_length=50, description="Suitor's orientation."
    )
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
    created_at: datetime = Field(description="Profile creation timestamp.")
    updated_at: datetime = Field(description="Profile update timestamp.")

    @computed_field(description="Whether required profile fields are complete.")
    @property
    def is_profile_complete(self) -> bool:
        """Whether required suitor profile fields are set."""
        return (
            self.age is not None
            and self.gender is not None
            and self.orientation is not None
        )


# Backward-compatible alias
SuitorRegisterResponse = SuitorProfileResponse
