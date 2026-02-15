"""Schemas for interview session APIs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.models.domain_enums import Verdict


class SessionStartRequest(BaseModel):
    """Session initialization payload."""

    heart_slug: str = Field(
        description="Shareable heart slug used to identify interview target."
    )


class SessionStartResponse(BaseModel):
    """Session initialization response payload."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str = Field(description="Created interview session UUID.")
    livekit_url: str = Field(
        description="LiveKit server URL used by the frontend client."
    )
    livekit_token: str = Field(description="LiveKit JWT for authenticated suitor join.")
    room_name: str = Field(description="LiveKit room name for this interview session.")
    status: str = Field(description="Session start status: ready or reconnecting.")
    message: str = Field(description="Human-readable start/reconnect message.")


class SessionStatusResponse(BaseModel):
    """Polling response for session status."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str = Field(description="Session UUID.")
    status: str = Field(
        description=(
            "Session state: pending, in_progress, completed, scoring, scored, "
            "expired, failed, cancelled."
        )
    )
    started_at: datetime | None = Field(
        default=None, description="Timestamp when interview started."
    )
    ended_at: datetime | None = Field(
        default=None, description="Timestamp when interview ended."
    )
    end_reason: str | None = Field(
        default=None, description="End reason when the session has finished."
    )
    duration_seconds: int | None = Field(
        default=None, description="Duration from start to end/current time."
    )
    questions_asked: int | None = Field(
        default=None, description="Number of questions asked so far."
    )
    questions_total: int | None = Field(
        default=None, description="Total configured screening questions."
    )
    has_verdict: bool = Field(description="Whether a final verdict exists.")
    verdict_status: str | None = Field(
        default=None, description="Verdict pipeline status: pending, scoring, ready."
    )


class SessionVerdictResponse(BaseModel):
    """Final verdict payload returned to suitor."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str = Field(description="Session UUID.")
    status: str = Field(description="Verdict status payload: scoring or scored.")
    ready: bool = Field(
        default=False, description="Whether a verdict is ready for this session."
    )
    verdict: Verdict | None = Field(default=None, description="Date/no-date verdict.")
    booking_available: bool | None = Field(
        default=None, description="True only when session verdict is date."
    )
    suitor_name: str | None = Field(
        default=None, description="Authenticated suitor name."
    )
    heart_name: str | None = Field(default=None, description="Heart display name.")
    message: str | None = Field(
        default=None, description="Status message for scoring state."
    )
    scores: dict | None = Field(
        default=None, description="Structured weighted scoring payload."
    )
    feedback: dict | None = Field(
        default=None, description="Structured feedback payload."
    )
    weighted_total: float | None = Field(
        default=None, description="Overall weighted score (0-100)."
    )
    raw_score: float | None = Field(
        default=None, description="Weighted score before final rounding."
    )
    final_score: float | None = Field(default=None, description="Final score (0-100).")
    effort_score: float | None = Field(
        default=None, description="Effort score (0-100)."
    )
    creativity_score: float | None = Field(
        default=None, description="Creativity score (0-100)."
    )
    intent_clarity_score: float | None = Field(
        default=None, description="Intent clarity score (0-100)."
    )
    emotional_intelligence_score: float | None = Field(
        default=None, description="Emotional intelligence score (0-100)."
    )
    feedback_text: str | None = Field(
        default=None, description="Personalized feedback for the suitor."
    )
    feedback_strengths: list[str] | None = Field(
        default=None, description="Top strengths identified during scoring."
    )
    feedback_improvements: list[str] | None = Field(
        default=None, description="Top areas for improvement."
    )
    per_question_scores: list[dict] | None = Field(
        default=None, description="Per-question scoring breakdown."
    )


# Backward-compatible aliases
StartSessionRequest = SessionStartRequest
StartSessionResponse = SessionStartResponse
VerdictResponse = SessionVerdictResponse


class SessionSummary(BaseModel):
    """Session summary item for suitor history."""

    session_id: str
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: int | None = None
    end_reason: str | None = None
    has_verdict: bool
    verdict: str | None = None
    final_score: float | None = None


class SuitorSessionsResponse(BaseModel):
    """Authenticated suitor session history response."""

    sessions: list[SessionSummary]
    total: int
    daily_limit: int
    remaining_today: int


class PreCheckResponse(BaseModel):
    """Readiness pre-check before creating a session."""

    can_start: bool
    reason: str | None = None
    profile_complete: bool
    heart_active: bool
    remaining_today: int
    active_session_id: str | None = None


class SlotTimeItem(BaseModel):
    """Single slot entry shown in grouped slot picker."""

    start: datetime
    end: datetime
    display: str


class SlotDayGroup(BaseModel):
    """Slots grouped by date for frontend rendering."""

    date: str
    day_label: str
    times: list[SlotTimeItem]


class SessionSlotsResponse(BaseModel):
    """Session-scoped slot response used in M6 results flow."""

    slots: list[SlotDayGroup]
    timezone: str
    event_duration_minutes: int


class SessionBookRequest(BaseModel):
    """Book a selected slot for a successful date verdict session."""

    slot_start: datetime
    suitor_name: str = Field(min_length=1, max_length=120)
    suitor_email: str = Field(min_length=3, max_length=255)
    suitor_notes: str | None = Field(default=None, max_length=1000)


class BookedSlotResponse(BaseModel):
    """Booked slot display payload."""

    start: datetime
    end: datetime
    display: str


class SessionBookResponse(BaseModel):
    """Booking confirmation payload for suitor."""

    booking_id: str
    cal_event_id: str
    slot: BookedSlotResponse
    status: str
    message: str
