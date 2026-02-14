"""Schemas for public profile endpoint."""

from pydantic import BaseModel, ConfigDict, Field


class PublicHeartProfileResponse(BaseModel):
    """Publicly exposed profile data."""

    model_config = ConfigDict(from_attributes=True)

    display_name: str = Field(description="Heart display name shown publicly.")
    bio_snippet: str | None = Field(
        default=None, description="Short public bio snippet."
    )
    avatar_preview_url: str | None = Field(
        default=None, description="Public avatar or photo preview URL."
    )
    shareable_slug: str = Field(description="Public slug used in the URL.")
