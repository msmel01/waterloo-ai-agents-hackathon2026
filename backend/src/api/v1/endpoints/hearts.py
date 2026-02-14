"""Heart domain endpoints."""

import uuid
from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from src.core.config import config
from src.core.container import Container
from src.core.security import get_current_user
from src.repository.conversation_turn_repository import ConversationTurnRepository
from src.repository.heart_repository import HeartRepository
from src.repository.score_repository import ScoreRepository
from src.repository.screening_question_repository import ScreeningQuestionRepository
from src.repository.session_repository import SessionRepository
from src.schemas.heart_schema import (
    DashboardStatsResponse,
    HeartProfileResponse,
    SessionDetailResponse,
    SessionDetailScore,
    SessionDetailTurn,
    SessionListResponse,
    SessionSummaryItem,
    ShareableLinkResponse,
    ToggleLinkRequest,
    ToggleLinkResponse,
    UpdateExpectationsRequest,
    UpdateHeartProfileRequest,
    UpdatePersonaRequest,
)
from src.schemas.screening_question_schema import (
    CreateScreeningQuestionRequest,
    ReorderScreeningQuestionsRequest,
    ScreeningQuestionListResponse,
    ScreeningQuestionResponse,
    UpdateScreeningQuestionRequest,
)

router = APIRouter(prefix="/hearts", tags=["hearts"])

CurrentUser = Annotated[str, Depends(get_current_user)]
HeartRepoDep = Annotated[HeartRepository, Depends(Provide[Container.heart_repository])]
QuestionRepoDep = Annotated[
    ScreeningQuestionRepository,
    Depends(Provide[Container.screening_question_repository]),
]
SessionRepoDep = Annotated[
    SessionRepository, Depends(Provide[Container.session_repository])
]
TurnRepoDep = Annotated[
    ConversationTurnRepository,
    Depends(Provide[Container.conversation_turn_repository]),
]
ScoreRepoDep = Annotated[ScoreRepository, Depends(Provide[Container.score_repository])]


def _frontend_public_url(slug: str) -> str:
    base = getattr(config, "FRONTEND_URL", "http://localhost:5173").rstrip("/")
    return f"{base}/hotline/{slug}"


async def _get_heart_or_404(clerk_user_id: str, heart_repo: HeartRepository):
    heart = await heart_repo.find_by_clerk_id(clerk_user_id)
    if not heart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Heart profile not found"
        )
    return heart


@router.get("/me", response_model=HeartProfileResponse)
@inject
async def get_me(current_user: CurrentUser, heart_repo: HeartRepoDep):
    """Get current authenticated heart profile."""
    return await _get_heart_or_404(current_user, heart_repo)


@router.put("/me", response_model=HeartProfileResponse)
@inject
async def update_me(
    payload: UpdateHeartProfileRequest,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
):
    """Update mutable heart profile fields."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(heart, field, value)
    return await heart_repo.update(heart.id, heart)


@router.put("/me/persona", response_model=HeartProfileResponse)
@inject
async def update_persona(
    payload: UpdatePersonaRequest,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
):
    """Update heart persona configuration."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    heart.persona = payload.persona.model_dump()
    return await heart_repo.update(heart.id, heart)


@router.put("/me/expectations", response_model=HeartProfileResponse)
@inject
async def update_expectations(
    payload: UpdateExpectationsRequest,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
):
    """Update heart expectation configuration."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    heart.expectations = payload.expectations.model_dump()
    return await heart_repo.update(heart.id, heart)


@router.get("/me/questions", response_model=ScreeningQuestionListResponse)
@inject
async def list_questions(
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """List all screening questions for the current heart."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    items = await question_repo.find_by_heart_id(heart.id)
    return ScreeningQuestionListResponse(
        items=[ScreeningQuestionResponse.model_validate(item) for item in items]
    )


@router.post(
    "/me/questions",
    response_model=ScreeningQuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def add_question(
    payload: CreateScreeningQuestionRequest,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """Create a screening question for the current heart."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    created = await question_repo.create(
        question_repo.model(
            heart_id=heart.id,
            question_text=payload.question_text,
            order_index=payload.order_index,
            is_required=payload.is_required,
        )
    )
    return ScreeningQuestionResponse.model_validate(created)


@router.post("/me/questions/reorder", response_model=ScreeningQuestionListResponse)
@inject
async def reorder_questions(
    payload: ReorderScreeningQuestionsRequest,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """Reorder screening questions in bulk."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    ordered = await question_repo.bulk_reorder(
        heart.id,
        [(item.id, item.order_index) for item in payload.items],
    )
    return ScreeningQuestionListResponse(
        items=[ScreeningQuestionResponse.model_validate(item) for item in ordered]
    )


@router.put("/me/questions/{question_id}", response_model=ScreeningQuestionResponse)
@inject
async def update_question(
    question_id: uuid.UUID,
    payload: UpdateScreeningQuestionRequest,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """Update a screening question by id."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    question = await question_repo.read_by_id(question_id)
    if question.heart_id != heart.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(question, field, value)

    updated = await question_repo.update(question_id, question)
    return ScreeningQuestionResponse.model_validate(updated)


@router.delete("/me/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_question(
    question_id: uuid.UUID,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """Delete a screening question by id."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    question = await question_repo.read_by_id(question_id)
    if question.heart_id != heart.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )
    await question_repo.delete_by_id(question_id)


@router.get("/me/link", response_model=ShareableLinkResponse)
@inject
async def get_shareable_link(current_user: CurrentUser, heart_repo: HeartRepoDep):
    """Get current heart shareable public link metadata."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    return ShareableLinkResponse(
        slug=heart.shareable_slug,
        url=_frontend_public_url(heart.shareable_slug),
        is_active=heart.is_active,
    )


@router.post("/me/link/toggle", response_model=ToggleLinkResponse)
@inject
async def toggle_link(
    payload: ToggleLinkRequest,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
):
    """Toggle public link active state."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    heart.is_active = payload.is_active
    updated = await heart_repo.update(heart.id, heart)
    return ToggleLinkResponse(slug=updated.shareable_slug, is_active=updated.is_active)


@router.get("/me/dashboard/stats", response_model=DashboardStatsResponse)
@inject
async def dashboard_stats(
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
):
    """Return basic dashboard statistics for the current heart."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    sessions = await session_repo.find_by_heart_id(heart.id)

    completed_sessions = [
        session for session in sessions if session.status.value == "completed"
    ]

    scores = []
    for session in sessions:
        score = await score_repo.find_by_session_id(session.id)
        if score:
            scores.append(score)

    date_verdicts = sum(1 for score in scores if score.verdict.value == "date")
    no_date_verdicts = sum(1 for score in scores if score.verdict.value == "no_date")
    avg_weighted = (
        sum(score.weighted_total for score in scores) / len(scores) if scores else 0.0
    )

    return DashboardStatsResponse(
        total_sessions=len(sessions),
        completed_sessions=len(completed_sessions),
        date_verdicts=date_verdicts,
        no_date_verdicts=no_date_verdicts,
        average_weighted_score=avg_weighted,
        upcoming_bookings=0,
    )


@router.get("/me/sessions", response_model=SessionListResponse)
@inject
async def list_sessions(
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
):
    """List all suitor sessions for the current heart."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    sessions = await session_repo.find_by_heart_id(heart.id)

    items: list[SessionSummaryItem] = []
    for session in sessions:
        score = await score_repo.find_by_session_id(session.id)
        items.append(
            SessionSummaryItem(
                id=session.id,
                suitor_id=session.suitor_id,
                suitor_name="Suitor",
                status=session.status.value,
                created_at=session.created_at,
                weighted_total=score.weighted_total if score else None,
                verdict=score.verdict.value if score else None,
            )
        )

    return SessionListResponse(sessions=items)


@router.get("/me/sessions/{session_id}", response_model=SessionDetailResponse)
@inject
async def session_detail(
    session_id: uuid.UUID,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    session_repo: SessionRepoDep,
    turn_repo: TurnRepoDep,
    score_repo: ScoreRepoDep,
):
    """Get detailed session artifact with transcript and score."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    session = await session_repo.read_by_id(session_id)

    if session.heart_id != heart.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    turns = await turn_repo.find_by_session_id(session.id)
    score = await score_repo.find_by_session_id(session.id)

    return SessionDetailResponse(
        session_id=session.id,
        heart_id=session.heart_id,
        suitor_id=session.suitor_id,
        suitor_name="Suitor",
        status=session.status.value,
        started_at=session.started_at,
        ended_at=session.ended_at,
        created_at=session.created_at,
        turns=[
            SessionDetailTurn(
                id=turn.id,
                turn_index=turn.turn_index,
                speaker=turn.speaker.value,
                content=turn.content,
                emotion_data=turn.emotion_data,
                duration_seconds=turn.duration_seconds,
                created_at=turn.created_at,
            )
            for turn in turns
        ],
        score=(
            SessionDetailScore(
                effort_score=score.effort_score,
                creativity_score=score.creativity_score,
                intent_clarity_score=score.intent_clarity_score,
                emotional_intelligence_score=score.emotional_intelligence_score,
                weighted_total=score.weighted_total,
                verdict=score.verdict.value,
                feedback_text=score.feedback_text,
            )
            if score
            else None
        ),
    )
