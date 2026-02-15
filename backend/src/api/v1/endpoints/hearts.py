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
from src.schemas.common_schema import PaginatedResponse, SuccessResponse
from src.schemas.heart_schema import (
    DashboardStatsResponse,
    ExpectationsUpdateRequest,
    HeartProfileResponse,
    HeartProfileUpdateRequest,
    PersonaUpdateRequest,
    QuestionSummary,
    SessionDetailResponse,
    SessionDetailScore,
    SessionDetailTurn,
    SessionListResponse,
    SessionSummaryItem,
    ShareableLinkResponse,
    ToggleLinkRequest,
    ToggleLinkResponse,
)
from src.schemas.screening_question_schema import (
    QuestionCreateRequest,
    QuestionResponse,
    QuestionsListResponse,
    QuestionsReorderRequest,
    QuestionUpdateRequest,
)

router = APIRouter(prefix="/hearts", tags=["Hearts"])

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


async def _to_heart_profile_response(
    heart, question_repo: ScreeningQuestionRepository
) -> HeartProfileResponse:
    questions = await question_repo.find_by_heart_id(heart.id)
    return HeartProfileResponse(
        id=heart.id,
        clerk_user_id=heart.clerk_user_id,
        email=heart.email,
        display_name=heart.display_name,
        bio=heart.bio,
        photo_url=heart.photo_url,
        video_url=heart.video_url,
        tavus_avatar_id=heart.tavus_avatar_id,
        persona=PersonaUpdateRequest.model_validate(heart.persona),
        expectations=ExpectationsUpdateRequest.model_validate(heart.expectations),
        questions=[
            QuestionSummary(
                id=question.id,
                question_text=question.question_text,
                order_index=question.order_index,
                is_required=question.is_required,
            )
            for question in questions
        ],
        calcom_user_id=heart.calcom_user_id,
        calcom_event_type_id=heart.calcom_event_type_id,
        shareable_slug=heart.shareable_slug,
        is_active=heart.is_active,
        created_at=heart.created_at,
        updated_at=heart.updated_at,
    )


@router.get("/me", response_model=HeartProfileResponse)
@inject
async def get_me(
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """Get the authenticated heart profile including persona, expectations, and screening questions."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    return await _to_heart_profile_response(heart, question_repo)


@router.put("/me", response_model=HeartProfileResponse)
@inject
async def update_me(
    payload: HeartProfileUpdateRequest,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """Update mutable heart profile fields for the authenticated heart."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(heart, field, value)
    updated = await heart_repo.update(heart.id, heart)
    return await _to_heart_profile_response(updated, question_repo)


@router.put("/me/persona", response_model=HeartProfileResponse)
@inject
async def update_persona(
    payload: PersonaUpdateRequest,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """Update persona settings used by the heart's AI avatar."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    heart.persona = payload.model_dump()
    updated = await heart_repo.update(heart.id, heart)
    return await _to_heart_profile_response(updated, question_repo)


@router.put("/me/expectations", response_model=HeartProfileResponse)
@inject
async def update_expectations(
    payload: ExpectationsUpdateRequest,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """Update dating expectations used for suitor evaluation."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    heart.expectations = payload.model_dump()
    updated = await heart_repo.update(heart.id, heart)
    return await _to_heart_profile_response(updated, question_repo)


@router.get(
    "/me/questions", response_model=QuestionsListResponse, tags=["Screening Questions"]
)
@inject
async def list_questions(
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """List screening questions configured for the authenticated heart."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    items = await question_repo.find_by_heart_id(heart.id)
    return QuestionsListResponse(
        items=[QuestionResponse.model_validate(item) for item in items]
    )


@router.post(
    "/me/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Screening Questions"],
)
@inject
async def add_question(
    payload: QuestionCreateRequest,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """Add a screening question for the authenticated heart profile."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    existing = await question_repo.find_by_heart_id(heart.id)
    created = await question_repo.create(
        question_repo.model(
            heart_id=heart.id,
            question_text=payload.question_text,
            order_index=len(existing) + 1,
            is_required=payload.is_required,
        )
    )
    return QuestionResponse.model_validate(created)


@router.put(
    "/me/questions/{id}", response_model=QuestionResponse, tags=["Screening Questions"]
)
@inject
async def update_question(
    id: uuid.UUID,
    payload: QuestionUpdateRequest,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """Update a specific screening question for the authenticated heart."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    question = await question_repo.read_by_id(id)
    if question.heart_id != heart.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(question, field, value)

    updated = await question_repo.update(id, question)
    return QuestionResponse.model_validate(updated)


@router.delete(
    "/me/questions/{id}", response_model=SuccessResponse, tags=["Screening Questions"]
)
@inject
async def delete_question(
    id: uuid.UUID,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """Delete a screening question from the authenticated heart profile."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    question = await question_repo.read_by_id(id)
    if question.heart_id != heart.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )
    await question_repo.delete_by_id(id)
    return SuccessResponse(message="Question deleted successfully.")


@router.post(
    "/me/questions/reorder",
    response_model=QuestionsListResponse,
    tags=["Screening Questions"],
)
@inject
async def reorder_questions(
    payload: QuestionsReorderRequest,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    question_repo: QuestionRepoDep,
):
    """Reorder screening questions by submitting a complete ordered list of question IDs."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    ordered = await question_repo.bulk_reorder(
        heart.id,
        [
            (question_id, index + 1)
            for index, question_id in enumerate(payload.question_ids)
        ],
    )
    return QuestionsListResponse(
        items=[QuestionResponse.model_validate(item) for item in ordered]
    )


@router.get("/me/link", response_model=ShareableLinkResponse)
@inject
async def get_shareable_link(current_user: CurrentUser, heart_repo: HeartRepoDep):
    """Get public shareable interview link metadata for the authenticated heart."""
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
    """Activate or deactivate the authenticated heart's public link."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    heart.is_active = payload.is_active
    updated = await heart_repo.update(heart.id, heart)
    return ToggleLinkResponse(slug=updated.shareable_slug, is_active=updated.is_active)


@router.get(
    "/me/dashboard/stats", response_model=DashboardStatsResponse, tags=["Dashboard"]
)
@inject
async def dashboard_stats(
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
):
    """Get dashboard statistics for the authenticated heart."""
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
    avg_weighted = (
        sum(score.weighted_total for score in scores) / len(scores) if scores else 0.0
    )
    match_rate = float((date_verdicts / len(scores)) * 100) if scores else 0.0

    return DashboardStatsResponse(
        total_suitors=len(sessions),
        match_rate=match_rate,
        avg_scores=avg_weighted,
        total_sessions=len(sessions),
        completed_sessions=len(completed_sessions),
        upcoming_bookings=0,
    )


@router.get(
    "/me/sessions",
    response_model=SessionListResponse,
    tags=["Dashboard"],
    responses={
        200: {
            "model": PaginatedResponse,
            "description": "Generic pagination contract template.",
        }
    },
)
@inject
async def list_sessions(
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
):
    """List session summaries for the authenticated heart dashboard."""
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
                status=session.status,
                created_at=session.created_at,
                weighted_total=score.weighted_total if score else None,
                verdict=score.verdict if score else None,
            )
        )

    return SessionListResponse(
        items=items, total=len(items), page=1, per_page=len(items) or 1
    )


@router.get(
    "/me/sessions/{id}", response_model=SessionDetailResponse, tags=["Dashboard"]
)
@inject
async def session_detail(
    id: uuid.UUID,
    current_user: CurrentUser,
    heart_repo: HeartRepoDep,
    session_repo: SessionRepoDep,
    turn_repo: TurnRepoDep,
    score_repo: ScoreRepoDep,
):
    """Get transcript and scoring details for a specific session."""
    heart = await _get_heart_or_404(current_user, heart_repo)
    session = await session_repo.read_by_id(id)

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
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        created_at=session.created_at,
        turns=[
            SessionDetailTurn(
                id=turn.id,
                turn_index=turn.turn_index,
                speaker=turn.speaker,
                content=turn.content,
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
                verdict=score.verdict,
                feedback_text=score.feedback_text,
            )
            if score
            else None
        ),
    )
