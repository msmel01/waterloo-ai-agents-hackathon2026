"""Schemas for interview session APIs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.models.domain_enums import SessionStatus, Verdict
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
    heart_id: uuid.UUID = Field(description="Heart UUID for the interview.")
    suitor_id: uuid.UUID = Field(
        description="Authenticated suitor UUID for the interview."
    )
    status: SessionStatus = Field(description="Current session lifecycle state.")
    livekit_room_name: str | None = Field(
        default=None, description="LiveKit room name if allocated."
    )
    livekit_token: str | None = Field(
        default=None, description="LiveKit access token placeholder for Milestone 1."
    )
    created_at: datetime = Field(description="Session creation timestamp.")


class SessionStatusResponse(BaseModel):
    """Polling response for session status."""

    model_config = ConfigDict(from_attributes=True)

    session_id: uuid.UUID = Field(description="Session UUID.")
    status: SessionStatus = Field(description="Current session processing status.")
    started_at: datetime | None = Field(
        default=None, description="Timestamp when interview started."
    )
    ended_at: datetime | None = Field(
        default=None, description="Timestamp when interview ended."
    )


class SessionVerdictResponse(BaseModel):
    """Final verdict payload returned to suitor."""

    model_config = ConfigDict(from_attributes=True)

    session_id: uuid.UUID = Field(description="Session UUID.")
    verdict: Verdict | None = Field(
        default=None, description="Date/no-date verdict when ready."
    )
    weighted_total: float | None = Field(
        default=None, description="Overall weighted score (0-100)."
    )
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
    emotion_modifiers: EmotionModifiers | None = Field(
        default=None, description="Emotion-based score modifiers."
    )
    feedback_text: str | None = Field(
        default=None, description="Personalized feedback for the suitor."
    )
    ready: bool = Field(description="Whether verdict and scoring are ready.")


# Backward-compatible aliases
StartSessionRequest = SessionStartRequest
StartSessionResponse = SessionStartResponse
VerdictResponse = SessionVerdictResponse
