"""Schemas for auth/webhook endpoints."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ClerkWebhookEventRequest(BaseModel):
    """Raw Clerk webhook payload envelope."""

    model_config = ConfigDict(extra="allow")

    type: str = Field(description="Clerk event type (for example: user.created).")
    data: dict[str, Any] = Field(description="Event payload object from Clerk.")
    object: str | None = Field(
        default=None, description="Webhook object type metadata."
    )
