"""Schemas for screening question APIs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuestionResponse(BaseModel):
    """Single screening question payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Question UUID.")
    heart_id: uuid.UUID = Field(description="Owning heart UUID.")
    question_text: str = Field(description="Question text shown to suitors.")
    order_index: int = Field(description="Display order for this question.")
    is_required: bool = Field(description="Whether suitor must answer this question.")
    created_at: datetime = Field(description="Question creation timestamp.")


class QuestionsListResponse(BaseModel):
    """Ordered screening question list payload."""

    model_config = ConfigDict(from_attributes=True)

    items: list[QuestionResponse] = Field(
        default_factory=list,
        description="Ordered list of screening questions.",
    )


class QuestionCreateRequest(BaseModel):
    """Create screening question payload."""

    question_text: str = Field(description="New screening question text.")
    is_required: bool = Field(
        default=True, description="Whether answering this question is mandatory."
    )


class QuestionUpdateRequest(BaseModel):
    """Update screening question payload."""

    question_text: str | None = Field(
        default=None, description="Updated question text."
    )
    is_required: bool | None = Field(default=None, description="Updated required flag.")


class QuestionsReorderRequest(BaseModel):
    """Bulk reorder payload by question ID sequence."""

    question_ids: list[uuid.UUID] = Field(
        default_factory=list,
        description="Question IDs in the desired final order.",
    )


# Backward-compatible aliases
ScreeningQuestionResponse = QuestionResponse
ScreeningQuestionListResponse = QuestionsListResponse
CreateScreeningQuestionRequest = QuestionCreateRequest
UpdateScreeningQuestionRequest = QuestionUpdateRequest
ReorderScreeningQuestionsRequest = QuestionsReorderRequest
