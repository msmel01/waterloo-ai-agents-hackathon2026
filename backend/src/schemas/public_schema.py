"""Schemas for public profile endpoint."""

from pydantic import BaseModel

from src.schemas.heart_schema import ExpectationsConfig, PersonaConfig


class PublicHeartProfileResponse(BaseModel):
    """Publicly exposed profile data."""

    display_name: str
    bio: str | None = None
    photo_url: str | None = None
    persona: PersonaConfig
    expectations: ExpectationsConfig
    screening_questions: list[str]
