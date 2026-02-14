"""Schemas for screening question APIs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScreeningQuestionResponse(BaseModel):
    """Single screening question payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    heart_id: uuid.UUID
    question_text: str
    order_index: int
    is_required: bool
    created_at: datetime


class ScreeningQuestionListResponse(BaseModel):
    """Ordered screening questions."""

    items: list[ScreeningQuestionResponse]


class CreateScreeningQuestionRequest(BaseModel):
    """Create screening question payload."""

    question_text: str
    order_index: int
    is_required: bool = True


class UpdateScreeningQuestionRequest(BaseModel):
    """Update screening question payload."""

    question_text: str | None = None
    order_index: int | None = None
    is_required: bool | None = None


class ReorderQuestionItem(BaseModel):
    """Single reorder instruction."""

    id: uuid.UUID
    order_index: int


class ReorderScreeningQuestionsRequest(BaseModel):
    """Bulk reorder payload."""

    items: list[ReorderQuestionItem]
