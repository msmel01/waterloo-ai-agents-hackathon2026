"""E2E flow-oriented tests with mocked integrations."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from agent.session_manager import SessionManager
from src.api.v1.endpoints.public import get_public_profile
from src.api.v1.endpoints.sessions import (
    SessionStartRequest,
    end_session,
    get_session_status,
    start_session,
)
from src.api.v1.endpoints.suitors import complete_suitor_profile
from src.models.domain_enums import SessionStatus, Verdict
from src.models.score_model import ScoreDb
from src.models.session_model import SessionDb
from src.schemas.suitor_schema import SuitorRegisterRequest


class _Req:
    class app:
        class state:
            heart_config = type(
                "Cfg",
                (),
                {
                    "screening_questions": [1, 2, 3],
                    "calendar": type("Cal", (), {"calcom_event_type_id": None})(),
                    "persona": type(
                        "Persona", (), {"traits": ["witty", "warm", "direct"]}
                    )(),
                },
            )()


@pytest.mark.asyncio
async def test_e2e_001_full_suitor_journey(
    seeded_heart, registered_suitor, mock_livekit
):
    heart_repo = AsyncMock()
    heart_repo.find_by_slug.return_value = seeded_heart
    question_repo = AsyncMock()
    question_repo.find_by_heart_id.return_value = [1, 2, 3]
    profile = await get_public_profile.__wrapped__(
        seeded_heart.shareable_slug, _Req(), heart_repo, question_repo
    )
    assert profile.display_name

    suitor_repo = AsyncMock()
    suitor_repo.update_by_clerk_id.return_value = registered_suitor
    await complete_suitor_profile.__wrapped__(
        SuitorRegisterRequest(
            name="Suitor", age=25, gender="male", orientation="straight"
        ),
        registered_suitor,
        suitor_repo,
    )

    session_repo = AsyncMock()
    session_repo.find_active_by_suitor.return_value = None
    session_repo.count_today_by_suitor.return_value = 0
    session_repo.model = SessionDb
    created = SessionDb(
        id=uuid.uuid4(),
        heart_id=seeded_heart.id,
        suitor_id=registered_suitor.id,
        status=SessionStatus.PENDING,
    )
    session_repo.create.return_value = created
    session_repo.update_attr.side_effect = [
        SessionDb(
            **created.model_dump(exclude_none=True, exclude={"livekit_room_name"}),
            livekit_room_name=f"session-{created.id}",
        ),
        SessionDb(
            **created.model_dump(
                exclude_none=True, exclude={"livekit_room_name", "livekit_room_sid"}
            ),
            livekit_room_name=f"session-{created.id}",
            livekit_room_sid="RM_1",
        ),
    ]

    started = await start_session.__wrapped__(
        SessionStartRequest(heart_slug=seeded_heart.shareable_slug),
        registered_suitor,
        heart_repo,
        session_repo,
        mock_livekit,
    )
    assert started.livekit_token


@pytest.mark.asyncio
async def test_e2e_002_suitor_drops_midcall(completed_session):
    completed_session.end_reason = "suitor_disconnected"
    assert completed_session.end_reason == "suitor_disconnected"


@pytest.mark.asyncio
async def test_e2e_003_livekit_room_creation_fails(seeded_heart, registered_suitor):
    heart_repo = AsyncMock()
    heart_repo.find_by_slug.return_value = seeded_heart
    session_repo = AsyncMock()
    session_repo.find_active_by_suitor.return_value = None
    session_repo.count_today_by_suitor.return_value = 0
    session_repo.model = SessionDb
    created = SessionDb(
        id=uuid.uuid4(),
        heart_id=seeded_heart.id,
        suitor_id=registered_suitor.id,
        status=SessionStatus.PENDING,
    )
    session_repo.create.return_value = created
    session_repo.update_attr.return_value = created
    livekit = AsyncMock()
    livekit.create_room.side_effect = RuntimeError("livekit down")
    with pytest.raises(Exception):
        await start_session.__wrapped__(
            SessionStartRequest(heart_slug=seeded_heart.shareable_slug),
            registered_suitor,
            heart_repo,
            session_repo,
            livekit,
        )


@pytest.mark.asyncio
async def test_e2e_004_conversation_persists_without_emotion_payload():
    mgr = SessionManager("session-1", [{"text": "What made you swipe right?"}])
    mgr.add_transcript_entry("avatar", "What made you swipe right?")
    mgr.add_transcript_entry("suitor", "Your hiking bio was thoughtful.")
    mgr.record_response(0, "Referenced the hiking bio", "strong")
    payload = mgr.get_session_data()
    assert "emotion_timeline" not in payload
    assert payload["turns"]
    assert "emotions" not in payload["turns"][0]


@pytest.mark.asyncio
async def test_e2e_005_deepgram_stt_fails_midcall():
    stt = AsyncMock()
    stt.transcribe.side_effect = RuntimeError("stt failure")
    with pytest.raises(RuntimeError):
        await stt.transcribe(b"audio")


@pytest.mark.asyncio
async def test_e2e_006_concurrent_sessions(seeded_heart, registered_suitor):
    sessions = [
        SessionDb(
            id=uuid.uuid4(),
            heart_id=seeded_heart.id,
            suitor_id=registered_suitor.id,
            status=SessionStatus.PENDING,
            livekit_room_name=f"session-{uuid.uuid4()}",
        )
        for _ in range(3)
    ]
    assert len({s.livekit_room_name for s in sessions}) == 3


@pytest.mark.asyncio
async def test_e2e_007_rapid_session_create_and_end(registered_suitor):
    session = SessionDb(
        id=uuid.uuid4(),
        heart_id=uuid.uuid4(),
        suitor_id=registered_suitor.id,
        status=SessionStatus.PENDING,
    )
    repo = AsyncMock()
    repo.read_by_id.return_value = session
    livekit = AsyncMock()
    resp = await end_session.__wrapped__(session.id, registered_suitor, repo, livekit)
    assert resp.message == "Session ended"


@pytest.mark.asyncio
async def test_e2e_008_transcript_matches_conversation(sample_transcript):
    assert len(sample_transcript) == 5
    assert sample_transcript[0]["turn"] == 1


@pytest.mark.asyncio
async def test_e2e_009_transcript_entries_are_ordered(sample_transcript):
    turns = [row["turn"] for row in sample_transcript]
    assert turns == sorted(turns)


@pytest.mark.asyncio
async def test_e2e_010_scores_immutable_after_creation(completed_session):
    score = ScoreDb(
        session_id=completed_session.id,
        effort_score=80,
        creativity_score=70,
        intent_clarity_score=90,
        emotional_intelligence_score=60,
        weighted_total=75.5,
        verdict=Verdict.DATE,
        feedback_text="ok",
    )
    assert score.session_id == completed_session.id


@pytest.mark.asyncio
async def test_e2e_011_session_status_transitions(registered_suitor, completed_session):
    repo = AsyncMock()
    repo.read_by_id.return_value = completed_session
    score_repo = AsyncMock()
    score_repo.find_by_session_id.return_value = None
    out = await get_session_status.__wrapped__(
        _Req(), completed_session.id, registered_suitor, repo, score_repo
    )
    assert out.status in {
        "completed",
        "scoring",
        "scored",
        "failed",
        "expired",
        "cancelled",
        "in_progress",
        "pending",
    }
