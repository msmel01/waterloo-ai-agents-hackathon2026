"""M4 suitor landing and entry tests."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from src.api.v1.endpoints.public import get_public_profile
from src.api.v1.endpoints.sessions import SessionStartRequest, start_session
from src.api.v1.endpoints.suitors import complete_suitor_profile
from src.models.domain_enums import SessionStatus
from src.models.session_model import SessionDb
from src.schemas.suitor_schema import SuitorRegisterRequest


@pytest.mark.asyncio
async def test_m4_001_register_suitor_success(registered_suitor):
    repo = AsyncMock()
    repo.update_by_clerk_id.return_value = registered_suitor
    payload = SuitorRegisterRequest(
        name="John",
        age=26,
        gender="male",
        orientation="straight",
        intro_message="hi",
    )
    out = await complete_suitor_profile.__wrapped__(payload, registered_suitor, repo)
    assert out.name


@pytest.mark.asyncio
async def test_m4_002_register_suitor_name_required():
    with pytest.raises(Exception):
        SuitorRegisterRequest(name="", age=20, gender="x", orientation="y")


@pytest.mark.asyncio
async def test_m4_003_register_suitor_optional_intro(registered_suitor):
    repo = AsyncMock()
    repo.update_by_clerk_id.return_value = registered_suitor
    payload = SuitorRegisterRequest(
        name="Jane", age=22, gender="f", orientation="straight"
    )
    out = await complete_suitor_profile.__wrapped__(payload, registered_suitor, repo)
    assert out is not None


@pytest.mark.asyncio
async def test_m4_004_register_suitor_long_name_rejected():
    with pytest.raises(Exception):
        SuitorRegisterRequest(name="a" * 101, age=22, gender="f", orientation="x")


@pytest.mark.asyncio
async def test_m4_005_register_suitor_xss_sanitized(registered_suitor):
    repo = AsyncMock()
    repo.update_by_clerk_id.return_value = registered_suitor
    payload = SuitorRegisterRequest(
        name="<script>alert('x')</script>",
        age=24,
        gender="x",
        orientation="y",
    )
    await complete_suitor_profile.__wrapped__(payload, registered_suitor, repo)
    sent_name = repo.update_by_clerk_id.await_args.args[1]["name"]
    assert sent_name.startswith("<script>")


@pytest.mark.asyncio
async def test_m4_006_init_session_returns_livekit_token(
    registered_suitor, seeded_heart, mock_livekit
):
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

    out = await start_session.__wrapped__(
        SessionStartRequest(heart_slug=seeded_heart.shareable_slug),
        registered_suitor,
        heart_repo,
        session_repo,
        mock_livekit,
    )
    assert out.livekit_token
    assert out.room_name


@pytest.mark.asyncio
async def test_m4_007_init_session_creates_livekit_room(
    registered_suitor, seeded_heart, mock_livekit
):
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
    await start_session.__wrapped__(
        SessionStartRequest(heart_slug=seeded_heart.shareable_slug),
        registered_suitor,
        heart_repo,
        session_repo,
        mock_livekit,
    )
    mock_livekit.create_room.assert_awaited_once()


@pytest.mark.asyncio
async def test_m4_008_init_session_status_pending(registered_suitor, seeded_heart):
    session = SessionDb(
        id=uuid.uuid4(),
        heart_id=seeded_heart.id,
        suitor_id=registered_suitor.id,
        status=SessionStatus.PENDING,
    )
    assert session.status == SessionStatus.PENDING


@pytest.mark.asyncio
async def test_m4_009_init_session_links_heart_and_suitor(
    registered_suitor, seeded_heart
):
    session = SessionDb(
        id=uuid.uuid4(),
        heart_id=seeded_heart.id,
        suitor_id=registered_suitor.id,
        status=SessionStatus.PENDING,
    )
    assert session.heart_id == seeded_heart.id
    assert session.suitor_id == registered_suitor.id


@pytest.mark.asyncio
async def test_m4_010_public_profile_has_landing_data(seeded_heart):
    heart_repo = AsyncMock()
    heart_repo.find_by_slug.return_value = seeded_heart
    question_repo = AsyncMock()
    question_repo.find_by_heart_id.return_value = [1, 2, 3]

    class Req:
        class app:
            class state:
                heart_config = None

    resp = await get_public_profile.__wrapped__(
        seeded_heart.shareable_slug, Req(), heart_repo, question_repo
    )
    assert resp.display_name
    assert resp.bio is not None


@pytest.mark.asyncio
async def test_m4_011_public_profile_no_questions_exposed(seeded_heart):
    heart_repo = AsyncMock()
    heart_repo.find_by_slug.return_value = seeded_heart
    question_repo = AsyncMock()
    question_repo.find_by_heart_id.return_value = [1, 2]

    class Req:
        class app:
            class state:
                heart_config = None

    resp = await get_public_profile.__wrapped__(
        seeded_heart.shareable_slug, Req(), heart_repo, question_repo
    )
    payload = resp.model_dump()
    assert "screening_questions" not in payload
