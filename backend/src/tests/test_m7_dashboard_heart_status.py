from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src.api.v1.endpoints.dashboard import (
    get_dashboard_heart_status,
    patch_dashboard_heart_status,
)
from src.api.v1.endpoints.public import get_public_profile
from src.api.v1.endpoints.sessions import start_session
from src.schemas.dashboard_schema import DashboardHeartStatusPatchRequest
from src.schemas.session_schema import SessionStartRequest


@pytest.mark.asyncio
async def test_m7_status_001_get_heart_status(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = make_fake_db_m7(
        [fake_result_builder_m7(scalar_value=0)], heart=m7_seeded_heart
    )
    out = await get_dashboard_heart_status(dashboard_request, "ok", db)
    assert out.slug == "melika"
    assert out.name == "Melika"
    assert isinstance(out.active, bool)
    assert out.link.endswith("/melika")


@pytest.mark.asyncio
async def test_m7_status_002_default_active(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = make_fake_db_m7(
        [fake_result_builder_m7(scalar_value=0)], heart=m7_seeded_heart
    )
    out = await get_dashboard_heart_status(dashboard_request, "ok", db)
    assert out.active is True


@pytest.mark.asyncio
async def test_m7_status_003_total_sessions_accurate(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = make_fake_db_m7(
        [fake_result_builder_m7(scalar_value=7)], heart=m7_seeded_heart
    )
    out = await get_dashboard_heart_status(dashboard_request, "ok", db)
    assert out.total_sessions == 7


@pytest.mark.asyncio
async def test_m7_status_004_pause_heart(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = make_fake_db_m7(
        [fake_result_builder_m7(scalar_value=0)], heart=m7_seeded_heart
    )
    out = await patch_dashboard_heart_status(
        DashboardHeartStatusPatchRequest(active=False), dashboard_request, "ok", db
    )
    assert out.active is False
    assert out.deactivated_at is not None


@pytest.mark.asyncio
async def test_m7_status_005_pause_sets_db_flag(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = make_fake_db_m7(
        [fake_result_builder_m7(scalar_value=0)], heart=m7_seeded_heart
    )
    _ = await patch_dashboard_heart_status(
        DashboardHeartStatusPatchRequest(active=False), dashboard_request, "ok", db
    )
    assert m7_seeded_heart.is_active is False
    assert m7_seeded_heart.deactivated_at is not None


@pytest.mark.asyncio
async def test_m7_status_006_paused_blocks_new_sessions(m7_seeded_heart):
    heart_repo = AsyncMock()
    heart_repo.find_by_slug.return_value = SimpleNamespace(
        id=m7_seeded_heart.id, is_active=False
    )

    session_repo = AsyncMock()
    livekit = AsyncMock()

    suitor = SimpleNamespace(
        id=uuid.uuid4(),
        name="Alex",
        age=28,
        gender="male",
        orientation="straight",
    )

    with pytest.raises(Exception) as exc:
        await start_session.__wrapped__(
            SessionStartRequest(heart_slug="melika"),
            suitor,
            heart_repo,
            session_repo,
            livekit,
        )
    assert "paused" in str(exc.value).lower() or "403" in str(exc.value)


@pytest.mark.asyncio
async def test_m7_status_007_paused_public_profile_shows_inactive(m7_seeded_heart):
    heart = SimpleNamespace(
        id=m7_seeded_heart.id,
        display_name=m7_seeded_heart.display_name,
        bio=m7_seeded_heart.bio,
        photo_url=None,
        calcom_event_type_id="evt_1",
        persona={"traits": ["kind"]},
        is_active=False,
    )
    heart_repo = AsyncMock()
    heart_repo.find_by_slug.return_value = heart
    question_repo = AsyncMock()
    question_repo.find_by_heart_id.return_value = [1, 2, 3]
    req = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(heart_config=None)))

    out = await get_public_profile.__wrapped__("melika", req, heart_repo, question_repo)
    assert out.active is False
    assert out.message is not None


@pytest.mark.asyncio
async def test_m7_status_008_paused_existing_sessions_unaffected(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = make_fake_db_m7(
        [fake_result_builder_m7(scalar_value=1)], heart=m7_seeded_heart
    )
    _ = await patch_dashboard_heart_status(
        DashboardHeartStatusPatchRequest(active=False), dashboard_request, "ok", db
    )
    assert m7_seeded_heart.is_active is False


@pytest.mark.asyncio
async def test_m7_status_009_pause_already_paused_is_idempotent(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = make_fake_db_m7(
        [
            fake_result_builder_m7(scalar_value=1),
            fake_result_builder_m7(scalar_value=1),
        ],
        heart=m7_seeded_heart,
    )
    first = await patch_dashboard_heart_status(
        DashboardHeartStatusPatchRequest(active=False), dashboard_request, "ok", db
    )
    first_dt = first.deactivated_at
    second = await patch_dashboard_heart_status(
        DashboardHeartStatusPatchRequest(active=False), dashboard_request, "ok", db
    )
    assert second.active is False
    assert second.deactivated_at is not None
    assert second.deactivated_at >= first_dt


@pytest.mark.asyncio
async def test_m7_status_010_resume_heart(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    m7_seeded_heart.is_active = False
    m7_seeded_heart.deactivated_at = datetime.now(timezone.utc)
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = make_fake_db_m7(
        [fake_result_builder_m7(scalar_value=2)], heart=m7_seeded_heart
    )
    out = await patch_dashboard_heart_status(
        DashboardHeartStatusPatchRequest(active=True), dashboard_request, "ok", db
    )
    assert out.active is True


@pytest.mark.asyncio
async def test_m7_status_011_resume_clears_deactivated_at(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    m7_seeded_heart.is_active = False
    m7_seeded_heart.deactivated_at = datetime.now(timezone.utc)
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = make_fake_db_m7(
        [fake_result_builder_m7(scalar_value=2)], heart=m7_seeded_heart
    )
    _ = await patch_dashboard_heart_status(
        DashboardHeartStatusPatchRequest(active=True), dashboard_request, "ok", db
    )
    assert m7_seeded_heart.is_active is True
    assert m7_seeded_heart.deactivated_at is None


@pytest.mark.asyncio
async def test_m7_status_012_resume_allows_new_sessions(m7_seeded_heart):
    heart_repo = AsyncMock()
    heart_repo.find_by_slug.return_value = SimpleNamespace(
        id=m7_seeded_heart.id, is_active=True
    )

    created = SimpleNamespace(
        id=uuid.uuid4(), livekit_room_name="room", status="pending"
    )
    session_repo = AsyncMock()
    session_repo.find_active_by_suitor.return_value = None
    session_repo.count_today_by_suitor.return_value = 0
    session_repo.model.return_value = created
    session_repo.create.return_value = created
    session_repo.update_attr.return_value = created

    livekit = AsyncMock()
    livekit.create_room.return_value = {"sid": "RM_123"}
    # generate_suitor_token is used synchronously in start_session.
    livekit.generate_suitor_token = Mock(return_value="token")

    suitor = SimpleNamespace(
        id=uuid.uuid4(),
        name="Alex",
        age=28,
        gender="male",
        orientation="straight",
    )

    out = await start_session.__wrapped__(
        SessionStartRequest(heart_slug="melika"),
        suitor,
        heart_repo,
        session_repo,
        livekit,
    )
    assert out.status in {"ready", "reconnecting"}


@pytest.mark.asyncio
async def test_m7_status_013_resume_already_active_is_idempotent(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = make_fake_db_m7(
        [fake_result_builder_m7(scalar_value=2)], heart=m7_seeded_heart
    )
    out = await patch_dashboard_heart_status(
        DashboardHeartStatusPatchRequest(active=True), dashboard_request, "ok", db
    )
    assert out.active is True


@pytest.mark.asyncio
async def test_m7_status_014_patch_missing_active_field():
    with pytest.raises(Exception):
        DashboardHeartStatusPatchRequest.model_validate({})


@pytest.mark.asyncio
async def test_m7_status_015_patch_invalid_active_type():
    with pytest.raises(Exception):
        DashboardHeartStatusPatchRequest.model_validate({"active": {"bad": True}})


@pytest.mark.asyncio
async def test_m7_status_016_status_requires_auth(client):
    get_resp = await client.get("/api/v1/dashboard/heart/status")
    patch_resp = await client.patch(
        "/api/v1/dashboard/heart/status", json={"active": False}
    )
    assert get_resp.status_code in (401, 422)
    assert patch_resp.status_code in (401, 422)
