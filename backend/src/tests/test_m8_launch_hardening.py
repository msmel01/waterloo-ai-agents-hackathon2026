"""M8 launch hardening tests."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src.api.v1.endpoints.sessions import start_session
from src.schemas.session_schema import SessionStartRequest


@pytest.mark.asyncio
async def test_m8_health_endpoint_available(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert "status" in payload
    assert "db" in payload


@pytest.mark.asyncio
async def test_m8_start_session_sets_consent_metadata(m7_seeded_heart):
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
    session_repo.count_active_by_heart.return_value = 0
    session_repo.model.return_value = created
    session_repo.create.return_value = created
    session_repo.update_attr.return_value = created

    livekit = AsyncMock()
    livekit.create_room.return_value = {"sid": "RM_123"}
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

    kwargs = session_repo.model.call_args.kwargs
    assert kwargs["consent_given_at"] is not None
    assert isinstance(kwargs["session_metadata"], dict)
    assert kwargs["session_metadata"]["consent"]["source"] == "chat_screen"
    assert out.status == "ready"
