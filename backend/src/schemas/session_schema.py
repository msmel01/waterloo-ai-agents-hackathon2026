"""Schemas for interview session APIs."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StartSessionRequest(BaseModel):
    """Session initialization payload."""

    heart_slug: str
    suitor_id: uuid.UUID


class StartSessionResponse(BaseModel):
    """Session start response."""

    session_id: uuid.UUID
    heart_id: uuid.UUID
    suitor_id: uuid.UUID
    status: str
    livekit_room_name: str | None = None
    created_at: datetime


class SessionStatusResponse(BaseModel):
    """Polling response for session status."""

    session_id: uuid.UUID
    status: str
    started_at: datetime | None = None
    ended_at: datetime | None = None


class VerdictResponse(BaseModel):
    """Final verdict payload returned to suitor."""

    session_id: uuid.UUID
    verdict: str | None = None
    weighted_total: float | None = None
    effort_score: float | None = None
    creativity_score: float | None = None
    intent_clarity_score: float | None = None
    emotional_intelligence_score: float | None = None
    emotion_modifiers: dict[str, Any] | None = None
    feedback_text: str | None = None
    ready: bool
