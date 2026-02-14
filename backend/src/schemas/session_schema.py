"""Schemas for interview session APIs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.models.domain_enums import Verdict
from src.schemas.heart_schema import EmotionModifiers


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
    verdict: Verdict = Field(description="Date/no-date verdict.")
    weighted_total: float = Field(description="Overall weighted score (0-100).")
    effort_score: float = Field(description="Effort score (0-100).")
    creativity_score: float = Field(description="Creativity score (0-100).")
    intent_clarity_score: float = Field(description="Intent clarity score (0-100).")
    emotional_intelligence_score: float = Field(
        description="Emotional intelligence score (0-100)."
    )
    emotion_modifiers: EmotionModifiers | None = Field(
        default=None, description="Emotion-based score modifiers."
    )
    feedback_text: str = Field(description="Personalized feedback for the suitor.")


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
