"""Schemas for heart profile and dashboard APIs."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PersonaConfig(BaseModel):
    """AI avatar persona configuration."""

    traits: list[str] = Field(default_factory=list)
    vibe: str = ""
    tone: str = ""
    humor_level: int = Field(default=0, ge=0, le=10)


class ExpectationsConfig(BaseModel):
    """Heart's dating expectations."""

    dealbreakers: list[str] = Field(default_factory=list)
    green_flags: list[str] = Field(default_factory=list)
    must_haves: list[str] = Field(default_factory=list)


class HeartProfileResponse(BaseModel):
    """Current heart profile payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clerk_user_id: str
    email: str
    display_name: str
    bio: str | None = None
    photo_url: str | None = None
    video_url: str | None = None
    tavus_avatar_id: str | None = None
    persona: PersonaConfig
    expectations: ExpectationsConfig
    calcom_user_id: str | None = None
    calcom_event_type_id: str | None = None
    shareable_slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UpdateHeartProfileRequest(BaseModel):
    """Mutable fields for heart profile updates."""

    display_name: str | None = None
    bio: str | None = None
    photo_url: str | None = None
    video_url: str | None = None
    calcom_user_id: str | None = None
    calcom_event_type_id: str | None = None


class UpdatePersonaRequest(BaseModel):
    """Request for persona updates."""

    persona: PersonaConfig


class UpdateExpectationsRequest(BaseModel):
    """Request for expectations updates."""

    expectations: ExpectationsConfig


class ShareableLinkResponse(BaseModel):
    """Public link metadata."""

    slug: str
    url: str
    is_active: bool


class ToggleLinkRequest(BaseModel):
    """Enable/disable public link."""

    is_active: bool


class ToggleLinkResponse(BaseModel):
    """Link state after toggle."""

    slug: str
    is_active: bool


class DashboardStatsResponse(BaseModel):
    """Dashboard summary card metrics."""

    total_sessions: int
    completed_sessions: int
    date_verdicts: int
    no_date_verdicts: int
    average_weighted_score: float
    upcoming_bookings: int


class SessionSummaryItem(BaseModel):
    """Compact session listing item for dashboard."""

    id: uuid.UUID
    suitor_id: uuid.UUID
    suitor_name: str
    status: str
    created_at: datetime
    weighted_total: float | None = None
    verdict: str | None = None


class SessionListResponse(BaseModel):
    """Session list response for a heart."""

    sessions: list[SessionSummaryItem]


class SessionDetailTurn(BaseModel):
    """Turn data in a detailed session response."""

    id: uuid.UUID
    turn_index: int
    speaker: str
    content: str
    emotion_data: dict[str, Any] | None = None
    duration_seconds: float | None = None
    created_at: datetime


class SessionDetailScore(BaseModel):
    """Scoring data in session details."""

    effort_score: float
    creativity_score: float
    intent_clarity_score: float
    emotional_intelligence_score: float
    weighted_total: float
    verdict: str
    feedback_text: str


class SessionDetailResponse(BaseModel):
    """Full session detail response payload."""

    session_id: uuid.UUID
    heart_id: uuid.UUID
    suitor_id: uuid.UUID
    suitor_name: str
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime
    turns: list[SessionDetailTurn]
    score: SessionDetailScore | None = None
