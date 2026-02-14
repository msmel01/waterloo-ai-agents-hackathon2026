"""Schemas for interview session APIs."""

import uuid
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

    session_id: uuid.UUID = Field(description="Created interview session UUID.")
    livekit_url: str = Field(
        description="LiveKit server URL used by the frontend client."
    )
    livekit_token: str = Field(description="LiveKit JWT for authenticated suitor join.")
    room_name: str = Field(description="LiveKit room name for this interview session.")


class SessionStatusResponse(BaseModel):
    """Polling response for session status."""

    model_config = ConfigDict(from_attributes=True)

    session_id: uuid.UUID = Field(description="Session UUID.")
    status: str = Field(
        description="Session state: pending, in_progress, completed, scoring, scored, failed, cancelled."
    )
    started_at: datetime | None = Field(
        default=None, description="Timestamp when interview started."
    )
    ended_at: datetime | None = Field(
        default=None, description="Timestamp when interview ended."
    )
    duration_seconds: float | None = Field(
        default=None, description="Duration from start to end/current time."
    )


class SessionVerdictResponse(BaseModel):
    """Final verdict payload returned to suitor."""

    model_config = ConfigDict(from_attributes=True)

    session_id: uuid.UUID = Field(description="Session UUID.")
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
