"""Schemas for suitor onboarding APIs."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class SuitorRegisterRequest(BaseModel):
    """Suitor registration payload."""

    name: str
    email: str | None = None
    intro_message: str | None = None


class SuitorRegisterResponse(BaseModel):
    """Suitor registration response."""

    id: uuid.UUID
    name: str
    email: str | None = None
    intro_message: str | None = None
    created_at: datetime
