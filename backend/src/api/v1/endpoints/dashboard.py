"""M7 simplified Heart dashboard endpoints."""

from __future__ import annotations

import math
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from src.dependencies import get_db_session, verify_dashboard_access
from src.models.booking_model import BookingDb
from src.models.domain_enums import SessionStatus, Verdict
from src.models.heart_model import HeartDb
from src.models.score_model import ScoreDb
from src.models.session_model import SessionDb
from src.models.suitor_model import SuitorDb
from src.schemas.dashboard_schema import (
    DashboardAvgScores,
    DashboardBookingBlock,
    DashboardBookingsStats,
    DashboardFeedbackBlock,
    DashboardHeartStatusPatchRequest,
    DashboardHeartStatusResponse,
    DashboardPagination,
    DashboardRecentActivity,
    DashboardScoreDistribution,
    DashboardScoresBlock,
    DashboardSessionBlock,
    DashboardSessionDetailResponse,
    DashboardSessionScores,
    DashboardSessionsResponse,
    DashboardSessionSummary,
    DashboardStatsResponse,
    DashboardSuitorBlock,
    DashboardTranscriptTurn,
    DashboardTrendPoint,
    DashboardTrendsResponse,
    DashboardWeightedScore,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

DashboardAuthDep = Annotated[str, Depends(verify_dashboard_access)]
DbDep = Annotated[AsyncSession, Depends(get_db_session)]

_STATS_CACHE: dict[str, tuple[datetime, DashboardStatsResponse]] = {}
_CACHE_TTL_SECONDS = 60

SCORE_LABELS: dict[str, tuple[float, str]] = {
    "effort": (0.30, "Effort & Thoughtfulness"),
    "creativity": (0.20, "Creativity & Originality"),
    "intent_clarity": (0.25, "Intent Clarity"),
    "emotional_intelligence": (0.25, "Emotional Intelligence"),
}


async def _resolve_heart(request: Request, db: AsyncSession) -> HeartDb:
    heart_id = getattr(request.app.state, "heart_id", None)
    heart: HeartDb | None = None
    if heart_id:
        heart = await db.get(HeartDb, heart_id)
    if heart is None:
        result = await db.execute(select(HeartDb).order_by(HeartDb.created_at.desc()))
        heart = result.scalars().first()
    if heart is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Heart profile not found"
        )
    return heart


def _round(value: float | None) -> float:
    return round(float(value or 0.0), 1)


def _extract_turns(turn_summaries: Any) -> list[dict[str, Any]]:
    if isinstance(turn_summaries, dict):
        turns = turn_summaries.get("turns")
        if isinstance(turns, list):
            return turns
    if isinstance(turn_summaries, list):
        return turn_summaries
    return []


def _session_duration_seconds(
    started_at: datetime | None, ended_at: datetime | None
) -> int | None:
    if not started_at or not ended_at:
        return None
    return int(max(0, (ended_at - started_at).total_seconds()))


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    request: Request,
    _auth: DashboardAuthDep,
    db: DbDep,
):
    heart = await _resolve_heart(request, db)
    cache_key = str(heart.id)
    now = datetime.now(timezone.utc)
    cached = _STATS_CACHE.get(cache_key)
    if cached and (now - cached[0]).total_seconds() < _CACHE_TTL_SECONDS:
        return cached[1]

    total_suitors = int(
        (await db.execute(select(func.count(SuitorDb.id)))).scalar() or 0
    )

    session_count_query = (
        select(SessionDb.status, func.count(SessionDb.id))
        .where(SessionDb.heart_id == heart.id)
        .group_by(SessionDb.status)
    )
    status_rows = (await db.execute(session_count_query)).all()
    status_counts = {
        row[0].value if hasattr(row[0], "value") else str(row[0]): int(row[1])
        for row in status_rows
    }

    total_sessions = sum(status_counts.values())
    active_sessions = status_counts.get(
        SessionStatus.PENDING.value, 0
    ) + status_counts.get(SessionStatus.IN_PROGRESS.value, 0)
    completed_sessions = (
        status_counts.get(SessionStatus.COMPLETED.value, 0)
        + status_counts.get(SessionStatus.SCORING.value, 0)
        + status_counts.get(SessionStatus.SCORED.value, 0)
    )
    failed_sessions = status_counts.get(SessionStatus.FAILED.value, 0)

    verdict_query = (
        select(ScoreDb.verdict, func.count(ScoreDb.id))
        .join(SessionDb, ScoreDb.session_id == SessionDb.id)
        .where(SessionDb.heart_id == heart.id)
        .group_by(ScoreDb.verdict)
    )
    verdict_rows = (await db.execute(verdict_query)).all()
    verdict_counts = {
        row[0].value if hasattr(row[0], "value") else str(row[0]): int(row[1])
        for row in verdict_rows
    }
    total_dates = verdict_counts.get(Verdict.DATE.value, 0)
    total_rejections = verdict_counts.get(Verdict.NO_DATE.value, 0)
    match_rate = (
        round((total_dates / completed_sessions) * 100, 1)
        if completed_sessions
        else 0.0
    )

    avg_query = (
        select(
            func.avg(ScoreDb.effort_score),
            func.avg(ScoreDb.creativity_score),
            func.avg(ScoreDb.intent_clarity_score),
            func.avg(ScoreDb.emotional_intelligence_score),
            func.avg(func.coalesce(ScoreDb.final_score, ScoreDb.weighted_total)),
        )
        .join(SessionDb, ScoreDb.session_id == SessionDb.id)
        .where(SessionDb.heart_id == heart.id)
    )
    avg_row = (await db.execute(avg_query)).one()
    avg_scores = DashboardAvgScores(
        effort=_round(avg_row[0]),
        creativity=_round(avg_row[1]),
        intent_clarity=_round(avg_row[2]),
        emotional_intelligence=_round(avg_row[3]),
        aggregate=_round(avg_row[4]),
    )

    tier_case = case(
        (func.coalesce(ScoreDb.final_score, ScoreDb.weighted_total) >= 80, "excellent"),
        (func.coalesce(ScoreDb.final_score, ScoreDb.weighted_total) >= 65, "good"),
        (func.coalesce(ScoreDb.final_score, ScoreDb.weighted_total) >= 50, "average"),
        else_="below_average",
    )
    tier_query = (
        select(tier_case.label("tier"), func.count(ScoreDb.id))
        .join(SessionDb, ScoreDb.session_id == SessionDb.id)
        .where(SessionDb.heart_id == heart.id)
        .group_by(tier_case)
    )
    tier_rows = (await db.execute(tier_query)).all()
    tiers = {"excellent": 0, "good": 0, "average": 0, "below_average": 0}
    for tier, count in tier_rows:
        tiers[str(tier)] = int(count)

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = day_start - timedelta(days=day_start.weekday())
    month_start = day_start.replace(day=1)
    sessions_today = int(
        (
            await db.execute(
                select(func.count(SessionDb.id)).where(
                    SessionDb.heart_id == heart.id, SessionDb.created_at >= day_start
                )
            )
        ).scalar()
        or 0
    )
    sessions_this_week = int(
        (
            await db.execute(
                select(func.count(SessionDb.id)).where(
                    SessionDb.heart_id == heart.id, SessionDb.created_at >= week_start
                )
            )
        ).scalar()
        or 0
    )
    sessions_this_month = int(
        (
            await db.execute(
                select(func.count(SessionDb.id)).where(
                    SessionDb.heart_id == heart.id, SessionDb.created_at >= month_start
                )
            )
        ).scalar()
        or 0
    )

    booking_total = int(
        (
            await db.execute(
                select(func.count(BookingDb.id)).where(BookingDb.heart_id == heart.id)
            )
        ).scalar()
        or 0
    )
    booking_upcoming = int(
        (
            await db.execute(
                select(func.count(BookingDb.id)).where(
                    BookingDb.heart_id == heart.id,
                    BookingDb.scheduled_at > now,
                )
            )
        ).scalar()
        or 0
    )
    booking_rate = round((booking_total / total_dates) * 100, 1) if total_dates else 0.0

    response = DashboardStatsResponse(
        total_suitors=total_suitors,
        total_sessions=total_sessions,
        completed_sessions=completed_sessions,
        active_sessions=active_sessions,
        failed_sessions=failed_sessions,
        total_dates=total_dates,
        total_rejections=total_rejections,
        match_rate=match_rate,
        avg_scores=avg_scores,
        score_distribution=DashboardScoreDistribution(**tiers),
        recent_activity=DashboardRecentActivity(
            sessions_today=sessions_today,
            sessions_this_week=sessions_this_week,
            sessions_this_month=sessions_this_month,
        ),
        bookings=DashboardBookingsStats(
            total_booked=booking_total,
            upcoming=booking_upcoming,
            booking_rate=booking_rate,
        ),
    )
    _STATS_CACHE[cache_key] = (now, response)
    return response


@router.get("/sessions", response_model=DashboardSessionsResponse)
async def get_dashboard_sessions(
    request: Request,
    _auth: DashboardAuthDep,
    db: DbDep,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    verdict: Literal["date", "no_date", "pending"] | None = Query(default=None),
    sort_by: Literal["date", "score", "name"] = Query(default="date"),
    sort_order: Literal["asc", "desc"] = Query(default="desc"),
    search: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
):
    heart = await _resolve_heart(request, db)

    aggregate_expr = func.coalesce(ScoreDb.final_score, ScoreDb.weighted_total)
    query = (
        select(
            SessionDb, SuitorDb, ScoreDb, BookingDb, aggregate_expr.label("aggregate")
        )
        .join(SuitorDb, SuitorDb.id == SessionDb.suitor_id)
        .outerjoin(ScoreDb, ScoreDb.session_id == SessionDb.id)
        .outerjoin(BookingDb, BookingDb.session_id == SessionDb.id)
        .where(SessionDb.heart_id == heart.id)
    )

    if verdict == "pending":
        query = query.where(ScoreDb.id.is_(None))
    elif verdict in {"date", "no_date"}:
        query = query.where(ScoreDb.verdict == Verdict(verdict))

    if search:
        query = query.where(col(SuitorDb.name).ilike(f"%{search.strip()}%"))

    if date_from:
        from_dt = datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        query = query.where(SessionDb.created_at >= from_dt)
    if date_to:
        to_dt = datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        query = query.where(SessionDb.created_at <= to_dt)

    if sort_by == "score":
        order_col = aggregate_expr
    elif sort_by == "name":
        order_col = SuitorDb.name
    else:
        order_col = func.coalesce(SessionDb.started_at, SessionDb.created_at)
    query = query.order_by(order_col.asc() if sort_order == "asc" else order_col.desc())

    count_query = (
        select(func.count(func.distinct(SessionDb.id)))
        .join(SuitorDb, SuitorDb.id == SessionDb.suitor_id)
        .outerjoin(ScoreDb, ScoreDb.session_id == SessionDb.id)
        .where(SessionDb.heart_id == heart.id)
    )
    if verdict == "pending":
        count_query = count_query.where(ScoreDb.id.is_(None))
    elif verdict in {"date", "no_date"}:
        count_query = count_query.where(ScoreDb.verdict == Verdict(verdict))
    if search:
        count_query = count_query.where(col(SuitorDb.name).ilike(f"%{search.strip()}%"))
    if date_from:
        count_query = count_query.where(
            SessionDb.created_at
            >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to:
        count_query = count_query.where(
            SessionDb.created_at
            <= datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        )

    total = int((await db.execute(count_query)).scalar() or 0)
    rows = (await db.execute(query.offset((page - 1) * per_page).limit(per_page))).all()

    sessions: list[DashboardSessionSummary] = []
    for session, suitor, score, booking, aggregate in rows:
        turns = _extract_turns(session.turn_summaries)
        duration = _session_duration_seconds(session.started_at, session.ended_at)
        scores_block = None
        verdict_value: Literal["date", "no_date", "pending"] = "pending"
        if score:
            scores_block = DashboardSessionScores(
                effort=float(score.effort_score),
                creativity=float(score.creativity_score),
                intent_clarity=float(score.intent_clarity_score),
                emotional_intelligence=float(score.emotional_intelligence_score),
                aggregate=float(aggregate or 0.0),
            )
            verdict_value = score.verdict.value

        sessions.append(
            DashboardSessionSummary(
                session_id=str(session.id),
                suitor_name=suitor.name,
                suitor_intro=suitor.intro_message,
                started_at=session.started_at,
                ended_at=session.ended_at,
                duration_seconds=duration,
                status=session.status.value,
                questions_asked=len(turns),
                scores=scores_block,
                verdict=verdict_value,
                has_booking=booking is not None,
                booking_date=booking.scheduled_at if booking else None,
            )
        )

    total_pages = max(1, math.ceil(total / per_page)) if total else 1
    return DashboardSessionsResponse(
        sessions=sessions,
        pagination=DashboardPagination(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        ),
    )


@router.get("/sessions/{session_id}", response_model=DashboardSessionDetailResponse)
async def get_dashboard_session_detail(
    session_id: uuid.UUID,
    request: Request,
    _auth: DashboardAuthDep,
    db: DbDep,
):
    heart = await _resolve_heart(request, db)
    query = (
        select(SessionDb, SuitorDb, ScoreDb, BookingDb)
        .join(SuitorDb, SuitorDb.id == SessionDb.suitor_id)
        .outerjoin(ScoreDb, ScoreDb.session_id == SessionDb.id)
        .outerjoin(BookingDb, BookingDb.session_id == SessionDb.id)
        .where(SessionDb.id == session_id, SessionDb.heart_id == heart.id)
    )
    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )

    session, suitor, score, booking = row
    turns = _extract_turns(session.turn_summaries)
    transcript = [
        DashboardTranscriptTurn(
            turn=int(item.get("turn", idx + 1)),
            question=str(item.get("question", "")),
            answer=str(item.get("answer", "")),
            timestamp=item.get("timestamp", ""),
        )
        for idx, item in enumerate(turns)
    ]

    scores_block = None
    feedback_block = None
    verdict_value: Literal["date", "no_date"] | None = None
    if score:
        aggregate = float(score.final_score or score.weighted_total or 0.0)
        scores_block = DashboardScoresBlock(
            effort=DashboardWeightedScore(
                score=float(score.effort_score),
                weight=SCORE_LABELS["effort"][0],
                label=SCORE_LABELS["effort"][1],
            ),
            creativity=DashboardWeightedScore(
                score=float(score.creativity_score),
                weight=SCORE_LABELS["creativity"][0],
                label=SCORE_LABELS["creativity"][1],
            ),
            intent_clarity=DashboardWeightedScore(
                score=float(score.intent_clarity_score),
                weight=SCORE_LABELS["intent_clarity"][0],
                label=SCORE_LABELS["intent_clarity"][1],
            ),
            emotional_intelligence=DashboardWeightedScore(
                score=float(score.emotional_intelligence_score),
                weight=SCORE_LABELS["emotional_intelligence"][0],
                label=SCORE_LABELS["emotional_intelligence"][1],
            ),
            aggregate=aggregate,
        )
        feedback_payload = (
            score.feedback_json if isinstance(score.feedback_json, dict) else {}
        )
        feedback_block = DashboardFeedbackBlock(
            summary=str(
                feedback_payload.get("summary")
                or score.feedback_summary
                or score.feedback_text
            ),
            strengths=list(
                feedback_payload.get("strengths") or score.feedback_strengths or []
            ),
            improvements=list(
                feedback_payload.get("improvements")
                or score.feedback_improvements
                or []
            ),
            favorite_moment=str(feedback_payload.get("favorite_moment") or ""),
        )
        verdict_value = score.verdict.value

    booking_block = None
    if booking:
        booking_block = DashboardBookingBlock(
            booking_id=str(booking.id),
            cal_event_id=booking.calcom_booking_id,
            booked_at=booking.created_at,
            slot_start=booking.scheduled_at,
            suitor_email=booking.suitor_email,
            suitor_notes=booking.suitor_notes,
            status=booking.status.value
            if hasattr(booking.status, "value")
            else str(booking.status),
        )

    return DashboardSessionDetailResponse(
        session_id=str(session.id),
        suitor=DashboardSuitorBlock(
            id=str(suitor.id),
            name=suitor.name,
            intro_message=suitor.intro_message,
            created_at=suitor.created_at,
        ),
        session=DashboardSessionBlock(
            status=session.status.value,
            started_at=session.started_at,
            ended_at=session.ended_at,
            duration_seconds=_session_duration_seconds(
                session.started_at, session.ended_at
            ),
            livekit_room_name=session.livekit_room_name,
        ),
        transcript=transcript,
        scores=scores_block,
        verdict=verdict_value,
        feedback=feedback_block,
        booking=booking_block,
    )


@router.get("/heart/status", response_model=DashboardHeartStatusResponse)
async def get_dashboard_heart_status(
    request: Request,
    _auth: DashboardAuthDep,
    db: DbDep,
):
    heart = await _resolve_heart(request, db)
    total_sessions = int(
        (
            await db.execute(
                select(func.count(SessionDb.id)).where(SessionDb.heart_id == heart.id)
            )
        ).scalar()
        or 0
    )
    base = str(getattr(request.app.state, "frontend_url", "") or "")
    if not base:
        from src.core.config import config

        base = config.FRONTEND_URL
    link = f"{base.rstrip('/')}/{heart.shareable_slug}"
    return DashboardHeartStatusResponse(
        slug=heart.shareable_slug,
        name=heart.display_name,
        active=heart.is_active,
        total_sessions=total_sessions,
        link=link,
        deactivated_at=heart.deactivated_at,
    )


@router.patch("/heart/status", response_model=DashboardHeartStatusResponse)
async def patch_dashboard_heart_status(
    payload: DashboardHeartStatusPatchRequest,
    request: Request,
    _auth: DashboardAuthDep,
    db: DbDep,
):
    heart = await _resolve_heart(request, db)
    now = datetime.now(timezone.utc)
    heart.is_active = payload.active
    heart.deactivated_at = None if payload.active else now
    db.add(heart)
    await db.commit()
    await db.refresh(heart)
    _STATS_CACHE.pop(str(heart.id), None)

    total_sessions = int(
        (
            await db.execute(
                select(func.count(SessionDb.id)).where(SessionDb.heart_id == heart.id)
            )
        ).scalar()
        or 0
    )
    from src.core.config import config

    message = (
        "Screening link has been reactivated."
        if payload.active
        else "Screening link has been paused. No new suitors can start interviews."
    )
    return DashboardHeartStatusResponse(
        slug=heart.shareable_slug,
        name=heart.display_name,
        active=heart.is_active,
        total_sessions=total_sessions,
        link=f"{config.FRONTEND_URL.rstrip('/')}/{heart.shareable_slug}",
        deactivated_at=heart.deactivated_at,
        message=message,
    )


@router.get("/stats/trends", response_model=DashboardTrendsResponse)
async def get_dashboard_trends(
    request: Request,
    _auth: DashboardAuthDep,
    db: DbDep,
    period: Literal["daily", "weekly"] = Query(default="daily"),
    days: int = Query(default=30, ge=1, le=365),
):
    heart = await _resolve_heart(request, db)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    trunc = "day" if period == "daily" else "week"
    bucket = func.date_trunc(trunc, SessionDb.started_at)
    aggregate_expr = func.coalesce(ScoreDb.final_score, ScoreDb.weighted_total)

    trend_query = (
        select(
            bucket.label("bucket"),
            func.count(SessionDb.id).label("sessions"),
            func.avg(aggregate_expr).label("avg_aggregate"),
            func.sum(case((ScoreDb.verdict == Verdict.DATE, 1), else_=0)).label(
                "dates"
            ),
            func.sum(case((ScoreDb.verdict == Verdict.NO_DATE, 1), else_=0)).label(
                "rejections"
            ),
        )
        .outerjoin(ScoreDb, ScoreDb.session_id == SessionDb.id)
        .where(
            SessionDb.heart_id == heart.id,
            SessionDb.status.in_(
                [SessionStatus.COMPLETED, SessionStatus.SCORING, SessionStatus.SCORED]
            ),
            or_(SessionDb.started_at.is_(None), SessionDb.started_at >= cutoff),
        )
        .group_by(bucket)
        .order_by(bucket.desc())
    )

    rows = (await db.execute(trend_query)).all()
    data = [
        DashboardTrendPoint(
            date=(row.bucket.date().isoformat() if row.bucket else ""),
            sessions=int(row.sessions or 0),
            avg_aggregate=round(float(row.avg_aggregate or 0.0), 1),
            dates=int(row.dates or 0),
            rejections=int(row.rejections or 0),
        )
        for row in rows
    ]
    return DashboardTrendsResponse(period=period, data=data)
