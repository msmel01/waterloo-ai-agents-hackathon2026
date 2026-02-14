"""Schemas for public profile endpoint."""

from pydantic import BaseModel, ConfigDict, Field


class PublicHeartProfileResponse(BaseModel):
    """Publicly exposed profile data."""

    model_config = ConfigDict(from_attributes=True)

    display_name: str = Field(description="Heart display name shown publicly.")
    bio: str | None = Field(default=None, description="Public bio text.")
    photo_url: str | None = Field(
        default=None, description="Public profile photo URL for the heart."
    )
    avatar_ready: bool = Field(
        description="Whether the voice interview agent stack is configured and ready."
    )
    has_calendar: bool = Field(
        description="Whether date booking is configured via cal.com."
    )
    question_count: int = Field(
        description="Number of screening questions the suitor will answer."
    )
    persona_preview: str | None = Field(
        default=None,
        description="Short personality teaser generated from top persona traits.",
    )
