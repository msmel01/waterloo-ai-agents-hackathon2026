"""Schemas for heart profile and dashboard APIs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.models.domain_enums import ConversationSpeaker, SessionStatus, Verdict
from src.schemas.common_schema import PaginatedResponse


class PersonaUpdateRequest(BaseModel):
    """Request body for persona updates."""

    traits: list[str] = Field(
        default_factory=list, description="Personality traits used by the AI avatar."
    )
    vibe: str = Field(
        default="", description="High-level vibe descriptor for the avatar."
    )
    tone: str = Field(default="", description="Conversation tone used by the avatar.")
    humor_level: int = Field(
        default=0, ge=0, le=10, description="Humor intensity from 0-10."
    )


class ExpectationsUpdateRequest(BaseModel):
    """Request body for expectation updates."""

    dealbreakers: list[str] = Field(
        default_factory=list, description="Non-negotiable disqualifiers."
    )
    green_flags: list[str] = Field(
        default_factory=list, description="Positive traits the heart values."
    )
    must_haves: list[str] = Field(
        default_factory=list, description="Must-have relationship requirements."
    )


class HeartProfileUpdateRequest(BaseModel):
    """Mutable fields for heart profile updates."""

    display_name: str | None = Field(
        default=None, description="Display name shown publicly."
    )
    bio: str | None = Field(default=None, description="Profile biography text.")
    photo_url: str | None = Field(default=None, description="Profile photo URL.")
    video_url: str | None = Field(default=None, description="Avatar source video URL.")
    calcom_user_id: str | None = Field(
        default=None, description="cal.com user identifier."
    )
    calcom_event_type_id: str | None = Field(
        default=None, description="cal.com event type identifier."
    )


class QuestionSummary(BaseModel):
    """Question summary embedded in heart profile payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Question UUID.")
    question_text: str = Field(description="Question text.")
    order_index: int = Field(description="Question ordering index.")
    is_required: bool = Field(description="Whether response is required.")


class HeartProfileResponse(BaseModel):
    """Current heart profile payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Heart UUID.")
    clerk_user_id: str = Field(description="Clerk user ID.")
    email: str = Field(description="Heart email address.")
    display_name: str = Field(description="Heart display name.")
    bio: str | None = Field(default=None, description="Heart biography.")
    photo_url: str | None = Field(default=None, description="Profile photo URL.")
    video_url: str | None = Field(default=None, description="Avatar source video URL.")
    tavus_avatar_id: str | None = Field(
        default=None, description="Generated Tavus avatar ID."
    )
    persona: PersonaUpdateRequest = Field(description="Avatar persona configuration.")
    expectations: ExpectationsUpdateRequest = Field(
        description="Dating expectation configuration."
    )
    questions: list[QuestionSummary] = Field(
        default_factory=list, description="Configured screening questions."
    )
    calcom_user_id: str | None = Field(default=None, description="cal.com user ID.")
    calcom_event_type_id: str | None = Field(
        default=None, description="cal.com event type ID."
    )
    shareable_slug: str = Field(
        description="Public slug used for the suitor entry page."
    )
    is_active: bool = Field(description="Whether the public interview link is active.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime = Field(description="Last update timestamp.")


class ShareableLinkResponse(BaseModel):
    """Public link metadata."""

    model_config = ConfigDict(from_attributes=True)

    slug: str = Field(description="Shareable profile slug.")
    url: str = Field(description="Fully-qualified frontend interview URL.")
    is_active: bool = Field(description="Whether the link is currently active.")


class ToggleLinkRequest(BaseModel):
    """Enable/disable public link."""

    is_active: bool = Field(description="New active flag for the shareable link.")


class ToggleLinkResponse(BaseModel):
    """Link state after toggle."""

    model_config = ConfigDict(from_attributes=True)

    slug: str = Field(description="Shareable profile slug.")
    is_active: bool = Field(description="Current active flag after toggle operation.")


class DashboardStatsResponse(BaseModel):
    """Dashboard summary card metrics."""

    model_config = ConfigDict(from_attributes=True)

    total_suitors: int = Field(description="Total suitors that entered screening.")
    match_rate: float = Field(description="Percentage of sessions with a date verdict.")
    avg_scores: float = Field(
        description="Average weighted score across completed sessions."
    )
    total_sessions: int = Field(description="Total sessions created.")
    completed_sessions: int = Field(description="Sessions with completed state.")
    upcoming_bookings: int = Field(description="Count of upcoming date bookings.")


class SessionSummaryItem(BaseModel):
    """Compact session listing item for dashboard."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Session UUID.")
    suitor_id: uuid.UUID = Field(description="Suitor UUID.")
    suitor_name: str = Field(description="Suitor display name.")
    status: SessionStatus = Field(description="Session lifecycle status.")
    created_at: datetime = Field(description="Session creation timestamp.")
    weighted_total: float | None = Field(
        default=None, description="Weighted total score if available."
    )
    verdict: Verdict | None = Field(
        default=None, description="Date/no-date verdict if available."
    )


class SessionListResponse(PaginatedResponse):
    """Paginated-style session list response for a heart."""

    model_config = ConfigDict(from_attributes=True)

    items: list[SessionSummaryItem] = Field(
        default_factory=list,
        description="Session summaries for dashboard list.",
    )


class SessionDetailTurn(BaseModel):
    """Turn data in a detailed session response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Conversation turn UUID.")
    turn_index: int = Field(description="Sequential turn index.")
    speaker: ConversationSpeaker = Field(
        description="Speaker role for the transcript entry."
    )
    content: str = Field(description="Transcript content.")
    duration_seconds: float | None = Field(
        default=None, description="Turn duration in seconds."
    )
    created_at: datetime = Field(description="Turn creation timestamp.")


class SessionDetailScore(BaseModel):
    """Scoring data in session details."""

    model_config = ConfigDict(from_attributes=True)

    effort_score: float = Field(description="Effort score (0-100).")
    creativity_score: float = Field(description="Creativity score (0-100).")
    intent_clarity_score: float = Field(description="Intent clarity score (0-100).")
    emotional_intelligence_score: float = Field(
        description="Emotional intelligence score (0-100)."
    )
    weighted_total: float = Field(description="Weighted total score (0-100).")
    verdict: Verdict = Field(description="Final verdict for this session.")
    feedback_text: str = Field(description="Personalized feedback summary.")


class SessionDetailResponse(BaseModel):
    """Full session detail response payload."""

    model_config = ConfigDict(from_attributes=True)

    session_id: uuid.UUID = Field(description="Session UUID.")
    heart_id: uuid.UUID = Field(description="Heart UUID.")
    suitor_id: uuid.UUID = Field(description="Suitor UUID.")
    suitor_name: str = Field(description="Suitor display name.")
    status: SessionStatus = Field(description="Current session status.")
    started_at: datetime | None = Field(
        default=None, description="Session start timestamp."
    )
    ended_at: datetime | None = Field(
        default=None, description="Session end timestamp."
    )
    created_at: datetime = Field(description="Session creation timestamp.")
    turns: list[SessionDetailTurn] = Field(
        default_factory=list, description="Ordered transcript turns."
    )
    score: SessionDetailScore | None = Field(
        default=None, description="Final score payload when available."
    )


# Backward-compatible aliases
UpdateHeartProfileRequest = HeartProfileUpdateRequest
UpdatePersonaRequest = PersonaUpdateRequest
UpdateExpectationsRequest = ExpectationsUpdateRequest
