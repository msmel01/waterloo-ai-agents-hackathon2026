"""Session endpoints."""

import json
import logging
import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Annotated
from zoneinfo import ZoneInfo

import httpx
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from src.core.config import config
from src.core.container import Container
from src.core.exceptions import NotFoundError
from src.dependencies import (
    get_calcom_service,
    get_current_suitor,
    get_livekit_service,
)
from src.models.domain_enums import BookingStatus, SessionStatus, Verdict
from src.models.suitor_model import SuitorDb
from src.repository.booking_repository import BookingRepository
from src.repository.heart_repository import HeartRepository
from src.repository.score_repository import ScoreRepository
from src.repository.session_repository import SessionRepository
from src.schemas.common_schema import SuccessResponse
from src.schemas.session_schema import (
    BookedSlotResponse,
    PreCheckResponse,
    SessionBookRequest,
    SessionBookResponse,
    SessionSlotsResponse,
    SessionStartRequest,
    SessionStartResponse,
    SessionStatusResponse,
    SessionVerdictResponse,
    SlotDayGroup,
    SlotTimeItem,
)
from src.services.calcom_service import CalcomService
from src.services.livekit_service import LiveKitService

router = APIRouter(prefix="/sessions", tags=["Sessions"])
logger = logging.getLogger(__name__)

try:
    from livekit.api import TwirpError
except ImportError:  # pragma: no cover - optional dependency guard
    TwirpError = RuntimeError  # type: ignore[assignment]

CurrentSuitor = Annotated[SuitorDb, Depends(get_current_suitor)]
HeartRepoDep = Annotated[HeartRepository, Depends(Provide[Container.heart_repository])]
SessionRepoDep = Annotated[
    SessionRepository, Depends(Provide[Container.session_repository])
]
ScoreRepoDep = Annotated[ScoreRepository, Depends(Provide[Container.score_repository])]
BookingRepoDep = Annotated[
    BookingRepository, Depends(Provide[Container.booking_repository])
]
LiveKitDep = Annotated[LiveKitService, Depends(get_livekit_service)]
CalcomDep = Annotated[CalcomService, Depends(get_calcom_service)]
AGENT_NAME = "valentine-interview-agent"
SCORE_LABELS: dict[str, tuple[float, str]] = {
    "effort": (0.30, "Effort & Thoughtfulness"),
    "creativity": (0.20, "Creativity & Originality"),
    "intent_clarity": (0.25, "Intent Clarity"),
    "emotional_intelligence": (0.25, "Emotional Intelligence"),
}


def _to_utc_iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _extract_slot_entries(
    raw_slots: object, duration_minutes: int
) -> list[tuple[datetime, datetime]]:
    entries: list[tuple[datetime, datetime]] = []

    def add_entry(start: datetime | None, end: datetime | None) -> None:
        if start is None:
            return
        resolved_end = end or (start + timedelta(minutes=duration_minutes))
        entries.append((start, resolved_end))

    if isinstance(raw_slots, list):
        for item in raw_slots:
            if isinstance(item, str):
                add_entry(_parse_dt(item), None)
                continue
            if not isinstance(item, dict):
                continue
            start = _parse_dt(
                item.get("start")
                or item.get("startTime")
                or item.get("startsAt")
                or item.get("time")
            )
            end = _parse_dt(
                item.get("end") or item.get("endTime") or item.get("endsAt")
            )
            add_entry(start, end)
        return entries

    if isinstance(raw_slots, dict):
        for key, value in raw_slots.items():
            if isinstance(value, list):
                for sub in value:
                    if isinstance(sub, str):
                        add_entry(_parse_dt(sub), None)
                    elif isinstance(sub, dict):
                        start = _parse_dt(
                            sub.get("start")
                            or sub.get("startTime")
                            or sub.get("startsAt")
                            or sub.get("time")
                        )
                        end = _parse_dt(
                            sub.get("end") or sub.get("endTime") or sub.get("endsAt")
                        )
                        add_entry(start, end)
            elif isinstance(value, dict):
                start = _parse_dt(
                    value.get("start")
                    or value.get("startTime")
                    or value.get("startsAt")
                    or key
                )
                end = _parse_dt(value.get("end") or value.get("endTime"))
                add_entry(start, end)
            elif isinstance(value, str):
                add_entry(_parse_dt(value), None)
        return entries

    return entries


def _group_slots(
    entries: list[tuple[datetime, datetime]],
    timezone_name: str,
) -> list[SlotDayGroup]:
    tz = ZoneInfo(timezone_name)
    grouped: dict[str, list[SlotTimeItem]] = defaultdict(list)

    for start_utc, end_utc in sorted(entries, key=lambda x: x[0]):
        local_start = start_utc.astimezone(tz)
        local_end = end_utc.astimezone(tz)  # noqa: F841
        day_key = local_start.date().isoformat()
        display = local_start.strftime("%I:%M %p").lstrip("0")
        grouped[day_key].append(
            SlotTimeItem(
                start=start_utc,
                end=end_utc,
                display=display,
            )
        )

    day_groups: list[SlotDayGroup] = []
    for day_key in sorted(grouped.keys()):
        local_date = datetime.fromisoformat(day_key).date()
        day_groups.append(
            SlotDayGroup(
                date=day_key,
                day_label=local_date.strftime("%A, %b %d"),
                times=grouped[day_key],
            )
        )
    return day_groups


def _feedback_payload(score) -> dict:
    payload = score.feedback_json if isinstance(score.feedback_json, dict) else None
    if payload:
        return {
            "summary": payload.get("summary")
            or score.feedback_summary
            or score.feedback_text,
            "strengths": payload.get("strengths") or score.feedback_strengths or [],
            "improvements": payload.get("improvements")
            or score.feedback_improvements
            or [],
            "favorite_moment": payload.get("favorite_moment") or "",
        }
    return {
        "summary": score.feedback_summary or score.feedback_text,
        "strengths": score.feedback_strengths or [],
        "improvements": score.feedback_improvements or [],
        "favorite_moment": "",
    }


async def _notify_booking_webhook(
    webhook_url: str | None,
    *,
    suitor_name: str,
    slot_display: str,
    aggregate_score: float,
    verdict: str,
    feedback_summary: str,
) -> bool:
    if not webhook_url:
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(
                webhook_url,
                json={
                    "event": "date_booked",
                    "suitor_name": suitor_name,
                    "slot": slot_display,
                    "aggregate_score": aggregate_score,
                    "verdict": verdict,
                    "feedback_summary": feedback_summary,
                },
            )
            return response.status_code < 300
    except httpx.HTTPError:
        logger.warning("Booking webhook failed for %s", webhook_url)
        return False


@router.post(
    "/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED
)
@inject
async def start_session(
    payload: SessionStartRequest,
    suitor: CurrentSuitor,
    heart_repo: HeartRepoDep,
    session_repo: SessionRepoDep,
    livekit: LiveKitDep,
):
    """Start a new interview session and return LiveKit join credentials."""
    if suitor.age is None or suitor.gender is None or suitor.orientation is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Please complete your profile before starting an interview "
                "(age, gender, orientation required)."
            ),
        )

    heart = await heart_repo.find_by_slug(payload.heart_slug)
    if not heart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Heart link not found"
        )
    if not heart.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Screening is currently paused. Check back later.",
        )
    active = await session_repo.find_active_by_suitor(suitor.id)
    if active:
        if not active.livekit_room_name:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have an active session that is missing room details.",
            )
        livekit_token = livekit.generate_suitor_token(
            room_name=active.livekit_room_name,
            suitor_id=str(suitor.id),
            suitor_name=suitor.name or "Suitor",
        )
        return SessionStartResponse(
            session_id=str(active.id),
            livekit_url=config.LIVEKIT_URL or "",
            livekit_token=livekit_token,
            room_name=active.livekit_room_name,
            status="reconnecting",
            message="You have an active session. Reconnecting...",
        )

    today_count = await session_repo.count_today_by_suitor(suitor.id)
    if today_count >= config.MAX_SESSIONS_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"You've reached the daily limit of {config.MAX_SESSIONS_PER_DAY} "
                "interviews. Try again tomorrow!"
            ),
        )

    draft = session_repo.model(
        heart_id=heart.id,
        suitor_id=suitor.id,
        status=SessionStatus.PENDING,
        livekit_room_name=None,
    )
    created = await session_repo.create(draft)
    room_name = f"session-{created.id}"
    created = await session_repo.update_attr(created.id, "livekit_room_name", room_name)

    room_metadata = json.dumps(
        {
            "session_id": str(created.id),
            "heart_id": str(heart.id),
            "suitor_id": str(suitor.id),
        }
    )
    try:
        room = await livekit.create_room(
            room_name=room_name,
            max_participants=2,
            metadata=room_metadata,
        )
        await livekit.create_agent_dispatch(
            room_name=room_name,
            agent_name=AGENT_NAME,
            metadata=room_metadata,
        )
        await session_repo.update_attr(created.id, "livekit_room_sid", room.get("sid"))
        suitor_name = suitor.name or "Suitor"
        livekit_token = livekit.generate_suitor_token(
            room_name=room_name,
            suitor_id=str(suitor.id),
            suitor_name=suitor_name,
        )
    except (RuntimeError, TwirpError) as exc:
        logger.exception("Failed to initialize LiveKit room for session %s", created.id)
        await session_repo.update_status(created.id, SessionStatus.FAILED)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to initialize LiveKit room",
        ) from exc
    finally:
        await livekit.close()

    return SessionStartResponse(
        session_id=str(created.id),
        livekit_url=config.LIVEKIT_URL or "",
        livekit_token=livekit_token,
        room_name=room_name,
        status="ready",
        message="Session created. Connect to start your interview!",
    )


@router.get("/{id}/status", response_model=SessionStatusResponse)
@inject
async def get_session_status(
    request: Request,
    id: uuid.UUID,
    suitor: CurrentSuitor,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
):
    """Get current processing state for a session owned by the authenticated suitor."""
    try:
        session = await session_repo.read_by_id(id)
    except NotFoundError:
        session = None
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.suitor_id != suitor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    duration_seconds: int | None = None
    if session.started_at:
        end_ref = session.ended_at or datetime.now(timezone.utc)
        duration_seconds = int(max(0.0, (end_ref - session.started_at).total_seconds()))

    turns_payload = session.turn_summaries or {}
    turns = turns_payload.get("turns", []) if isinstance(turns_payload, dict) else []
    questions_asked = len(turns) if turns else None

    heart_config = getattr(request.app.state, "heart_config", None)
    questions_total: int | None = None
    if heart_config and getattr(heart_config, "screening_questions", None) is not None:
        questions_total = len(heart_config.screening_questions)

    status_value = session.status.value
    score = await score_repo.find_by_session_id(session.id)
    has_verdict = bool(session.has_verdict or score is not None)
    verdict_status = session.verdict_status or ("ready" if score else "pending")

    return SessionStatusResponse(
        session_id=str(session.id),
        status=status_value,
        started_at=session.started_at,
        ended_at=session.ended_at,
        end_reason=session.end_reason,
        duration_seconds=duration_seconds,
        questions_asked=questions_asked,
        questions_total=questions_total,
        has_verdict=has_verdict,
        verdict_status=verdict_status,
    )


@router.post("/{id}/end", response_model=SuccessResponse)
@inject
async def end_session(
    id: uuid.UUID,
    suitor: CurrentSuitor,
    session_repo: SessionRepoDep,
    livekit: LiveKitDep,
):
    """End an active session and clean up the LiveKit room."""
    try:
        session = await session_repo.read_by_id(id)
    except NotFoundError:
        session = None
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.suitor_id != suitor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    now = datetime.now(timezone.utc)
    await session_repo.update_attr(id, "ended_at", now)
    await session_repo.update_attr(id, "end_reason", "manual_end")
    if session.status in {SessionStatus.PENDING, SessionStatus.IN_PROGRESS}:
        await session_repo.update_status(id, SessionStatus.COMPLETED)

    if session.livekit_room_name:
        try:
            await livekit.delete_room(session.livekit_room_name)
        finally:
            await livekit.close()

    return SuccessResponse(message="Session ended")


@router.get("/pre-check", response_model=PreCheckResponse)
@inject
async def pre_check(
    request: Request,
    suitor: CurrentSuitor,
    heart_repo: HeartRepoDep,
    session_repo: SessionRepoDep,
):
    """Check whether a suitor can start a new interview session."""
    heart_id = getattr(request.app.state, "heart_id", None)
    heart = None
    if heart_id:
        try:
            heart = await heart_repo.read_by_id(heart_id)
        except NotFoundError:
            heart = None
    profile_complete = bool(
        suitor.age is not None
        and suitor.gender is not None
        and suitor.orientation is not None
    )
    heart_active = bool(heart and heart.is_active)
    active_session = await session_repo.find_active_by_suitor(suitor.id)

    today_count = await session_repo.count_today_by_suitor(suitor.id)
    remaining = max(0, config.MAX_SESSIONS_PER_DAY - today_count)

    can_start = True
    reason: str | None = None
    if not profile_complete:
        can_start = False
        reason = "Please complete your profile first."
    elif not heart_active:
        can_start = False
        reason = "Interviews are currently paused."
    elif active_session:
        can_start = False
        reason = "You have an active interview session."
    elif remaining <= 0:
        can_start = False
        reason = f"You've reached the daily limit of {config.MAX_SESSIONS_PER_DAY} interviews."

    return PreCheckResponse(
        can_start=can_start,
        reason=reason,
        profile_complete=profile_complete,
        heart_active=heart_active,
        remaining_today=remaining,
        active_session_id=str(active_session.id) if active_session else None,
    )


@router.get("/{id}/verdict", response_model=SessionVerdictResponse)
@inject
async def get_session_verdict(
    id: uuid.UUID,
    suitor: CurrentSuitor,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
    heart_repo: HeartRepoDep,
):
    """Get verdict payload for results page with booking eligibility."""
    try:
        session = await session_repo.read_by_id(id)
    except NotFoundError:
        session = None
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.suitor_id != suitor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    if session.status in {SessionStatus.PENDING, SessionStatus.IN_PROGRESS}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has not ended yet.",
        )

    score = await score_repo.find_by_session_id(session.id)
    verdict_status = session.verdict_status or ("ready" if score else "pending")
    if verdict_status in {"pending", "scoring"} or not score:
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "session_id": str(session.id),
                "status": "scoring",
                "ready": False,
                "message": "Your results are being prepared. Please wait...",
            },
        )

    if verdict_status == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Scoring failed. Please try again later.",
        )

    heart = await heart_repo.read_by_id(session.heart_id)
    feedback = _feedback_payload(score)
    aggregate = float(score.final_score or score.weighted_total or 0.0)
    scores_payload = {
        key: {
            "score": float(getattr(score, f"{key}_score")),
            "weight": weight,
            "label": label,
        }
        for key, (weight, label) in SCORE_LABELS.items()
    }
    scores_payload["aggregate"] = round(aggregate, 2)

    return SessionVerdictResponse(
        session_id=str(session.id),
        status="scored",
        ready=True,
        verdict=score.verdict,
        booking_available=True if score.verdict == Verdict.DATE else None,
        suitor_name=suitor.name,
        heart_name=heart.display_name if heart else None,
        scores=scores_payload,
        feedback=feedback,
        weighted_total=score.weighted_total,
        raw_score=score.raw_score,
        final_score=score.final_score,
        effort_score=score.effort_score,
        creativity_score=score.creativity_score,
        intent_clarity_score=score.intent_clarity_score,
        emotional_intelligence_score=score.emotional_intelligence_score,
        feedback_text=feedback.get("summary"),
        feedback_strengths=feedback.get("strengths"),
        feedback_improvements=feedback.get("improvements"),
        per_question_scores=score.per_question_scores,
    )


@router.get("/{id}/slots", response_model=SessionSlotsResponse)
@inject
async def get_session_slots(
    request: Request,
    id: uuid.UUID,
    suitor: CurrentSuitor,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
    booking_repo: BookingRepoDep,
    calcom: CalcomDep,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
):
    """Get grouped available slots for date-eligible sessions."""
    try:
        session = await session_repo.read_by_id(id)
    except NotFoundError:
        session = None
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.suitor_id != suitor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    score = await score_repo.find_by_session_id(session.id)
    if not score or score.verdict != Verdict.DATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Booking not available for this session",
        )
    existing_booking = await booking_repo.find_by_session_id(session.id)
    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A date has already been booked for this session",
        )

    heart_config = getattr(request.app.state, "heart_config", None)
    timezone_name = "America/Toronto"
    duration_minutes = 60
    if heart_config and getattr(heart_config, "calendar", None):
        timezone_name = getattr(heart_config.calendar, "timezone", timezone_name)
        duration_minutes = int(
            getattr(heart_config.calendar, "event_duration_minutes", duration_minutes)
        )

    from_day = date_from or datetime.now(timezone.utc).date()
    to_day = date_to or (from_day + timedelta(days=14))
    if to_day < from_day:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="date_to must be on or after date_from",
        )

    start_dt = datetime.combine(from_day, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(to_day, time.max, tzinfo=timezone.utc)

    try:
        raw_slots = await calcom.get_available_slots(
            _to_utc_iso(start_dt), _to_utc_iso(end_dt)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to fetch availability. Please try again.",
        ) from exc

    entries = _extract_slot_entries(raw_slots, duration_minutes)
    grouped = _group_slots(entries, timezone_name)
    return SessionSlotsResponse(
        slots=grouped,
        timezone=timezone_name,
        event_duration_minutes=duration_minutes,
    )


@router.post(
    "/{id}/book",
    response_model=SessionBookResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_session_booking(
    request: Request,
    id: uuid.UUID,
    payload: SessionBookRequest,
    suitor: CurrentSuitor,
    session_repo: SessionRepoDep,
    score_repo: ScoreRepoDep,
    booking_repo: BookingRepoDep,
    calcom: CalcomDep,
):
    """Book a date slot for a session that received a date verdict."""
    try:
        session = await session_repo.read_by_id(id)
    except NotFoundError:
        session = None
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    if session.suitor_id != suitor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    score = await score_repo.find_by_session_id(session.id)
    if not score or score.verdict != Verdict.DATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Booking not available for this session",
        )

    existing_booking = await booking_repo.find_by_session_id(session.id)
    if existing_booking:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A date has already been booked for this session",
        )

    heart_config = getattr(request.app.state, "heart_config", None)
    timezone_name = "America/Toronto"
    duration_minutes = 60
    webhook_url = None
    if heart_config and getattr(heart_config, "calendar", None):
        timezone_name = getattr(heart_config.calendar, "timezone", timezone_name)
        duration_minutes = int(
            getattr(heart_config.calendar, "event_duration_minutes", duration_minutes)
        )
        webhook_url = getattr(heart_config.calendar, "notification_webhook_url", None)

    window_start = payload.slot_start.astimezone(timezone.utc) - timedelta(days=1)
    window_end = payload.slot_start.astimezone(timezone.utc) + timedelta(days=1)
    try:
        raw_slots = await calcom.get_available_slots(
            _to_utc_iso(window_start), _to_utc_iso(window_end)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to fetch availability. Please try again.",
        ) from exc

    entries = _extract_slot_entries(raw_slots, duration_minutes)
    selected: tuple[datetime, datetime] | None = None
    target = payload.slot_start.astimezone(timezone.utc).replace(microsecond=0)
    for start_dt, end_dt in entries:
        if start_dt.replace(microsecond=0) == target:
            selected = (start_dt, end_dt)
            break
    if selected is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This time slot is no longer available. Please choose another.",
        )

    try:
        booking_payload = await calcom.create_booking(
            slot_start=_to_utc_iso(selected[0]),
            attendee_name=payload.suitor_name,
            attendee_email=payload.suitor_email,
            notes=payload.suitor_notes,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to create booking. Please try another slot.",
        ) from exc

    cal_event_id = (
        str(booking_payload.get("id"))
        or str(booking_payload.get("uid"))
        or str(booking_payload.get("bookingId"))
    )
    if cal_event_id in {"None", ""}:
        data = (
            booking_payload.get("data") if isinstance(booking_payload, dict) else None
        )
        if isinstance(data, dict):
            cal_event_id = str(
                data.get("id") or data.get("uid") or f"cal_{uuid.uuid4().hex[:12]}"
            )
        else:
            cal_event_id = f"cal_{uuid.uuid4().hex[:12]}"

    local_start = selected[0].astimezone(ZoneInfo(timezone_name))
    slot_display = local_start.strftime("%A, %b %d at %I:%M %p").replace(" 0", " ")
    notification_sent = await _notify_booking_webhook(
        webhook_url,
        suitor_name=payload.suitor_name,
        slot_display=slot_display,
        aggregate_score=float(score.final_score or score.weighted_total or 0),
        verdict=score.verdict.value,
        feedback_summary=score.feedback_summary or score.feedback_text,
    )

    booking = await booking_repo.create(
        booking_repo.model(
            session_id=session.id,
            heart_id=session.heart_id,
            suitor_id=session.suitor_id,
            calcom_booking_id=cal_event_id,
            suitor_email=payload.suitor_email,
            suitor_notes=payload.suitor_notes,
            notification_sent=notification_sent,
            booking_status=BookingStatus.CONFIRMED.value,
            scheduled_at=selected[0],
            status=BookingStatus.CONFIRMED,
        )
    )

    return SessionBookResponse(
        booking_id=str(booking.id),
        cal_event_id=cal_event_id,
        slot=BookedSlotResponse(
            start=selected[0],
            end=selected[1],
            display=slot_display,
        ),
        status="confirmed",
        message="Your date has been booked! 💚",
    )
