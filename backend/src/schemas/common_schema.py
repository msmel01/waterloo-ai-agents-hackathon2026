"""Shared response schemas for API consistency and documentation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SuccessResponse(BaseModel):
    """Generic success message payload."""

    model_config = ConfigDict(from_attributes=True)

    message: str = Field(description="Human-readable success message.")


class ErrorResponse(BaseModel):
    """Standard API error payload."""

    model_config = ConfigDict(from_attributes=True)

    detail: str = Field(description="Primary error detail shown to API clients.")
    code: str | None = Field(
        default=None, description="Optional machine-readable error code."
    )


class PaginatedResponse(BaseModel):
    """Standard paginated list payload."""

    model_config = ConfigDict(from_attributes=True)

    items: list[Any] = Field(default_factory=list, description="Current page items.")
    total: int = Field(description="Total items across all pages.")
    page: int = Field(description="Current page number (1-indexed).")
    per_page: int = Field(description="Maximum items per page.")
