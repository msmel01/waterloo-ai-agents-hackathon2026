"""Schemas for admin endpoints."""

from pydantic import BaseModel, ConfigDict, Field


class TavusStatusInfo(BaseModel):
    """Tavus replica health information."""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(description="not_started | processing | ready | failed")
    replica_id: str | None = Field(
        default=None, description="Current Tavus replica ID if available."
    )


class CalcomStatusInfo(BaseModel):
    """cal.com integration health information."""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(description="connected | not_configured | error")
    event_type_id: str | None = Field(
        default=None, description="Configured cal.com event type ID."
    )


class SystemHealthResponse(BaseModel):
    """Top-level system health response."""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(description="healthy | degraded | unhealthy")
    heart_loaded: bool = Field(description="Whether a Heart record is available in DB.")
    heart_name: str | None = Field(
        default=None, description="Current heart display name."
    )
    heart_slug: str | None = Field(
        default=None, description="Current heart shareable slug."
    )
    database: str = Field(description="connected | error")
    redis: str = Field(description="connected | error")
    tavus: TavusStatusInfo = Field(description="Tavus subsystem health details.")
    calcom: CalcomStatusInfo = Field(description="cal.com subsystem health details.")


class AvatarCreateResponse(BaseModel):
    """Response for avatar creation trigger endpoint."""

    model_config = ConfigDict(from_attributes=True)

    replica_id: str = Field(description="Replica ID created or reused.")
    status: str = Field(description="processing | ready | failed")
    message: str = Field(description="Human-readable status message.")


class LinkToggleRequest(BaseModel):
    """Payload to activate/deactivate heart link."""

    is_active: bool = Field(
        description="Whether the public heart link should be active."
    )


class CalendarStatusResponse(BaseModel):
    """Calendar status response with lightweight slot preview."""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(description="connected | not_configured | error")
    event_type_id: str | None = Field(
        default=None, description="Configured event type ID."
    )
    slot_preview: list[str] = Field(
        default_factory=list, description="Preview list of upcoming slot timestamps."
    )
