"""Unit tests for stale session cleanup worker task."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.models.domain_enums import SessionStatus
from src.models.session_model import SessionDb
from workers import main as workers_main


@pytest.mark.asyncio
async def test_cleanup_stale_sessions_uses_repository_methods(monkeypatch):
    stale_pending = SessionDb(
        id=uuid.uuid4(),
        heart_id=uuid.uuid4(),
        suitor_id=uuid.uuid4(),
        status=SessionStatus.PENDING,
    )
    stale_pending.created_at = datetime.now(timezone.utc) - timedelta(hours=1)

    stale_progress = SessionDb(
        id=uuid.uuid4(),
        heart_id=uuid.uuid4(),
        suitor_id=uuid.uuid4(),
        status=SessionStatus.IN_PROGRESS,
        started_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )

    calls: list[tuple[str, object, object]] = []

    class FakeSessionRepository:
        def __init__(self, session_factory):
            self.session_factory = session_factory

        async def find_stale_pending(self, older_than):
            return [stale_pending]

        async def find_stale_in_progress(self, older_than):
            return [stale_progress]

        async def update_status(self, session_id, status):
            calls.append(("update_status", session_id, status))
            return None

        async def update_attr(self, session_id, column, value):
            calls.append(("update_attr", session_id, (column, value)))
            return None

    fake_db = SimpleNamespace(session=lambda: None)

    monkeypatch.setattr(workers_main, "database", fake_db)
    monkeypatch.setattr(workers_main, "SessionRepository", FakeSessionRepository)
    monkeypatch.setattr(workers_main.config, "SESSION_PENDING_TIMEOUT", 300)
    monkeypatch.setattr(workers_main.config, "SESSION_MAX_DURATION", 1800)

    result = await workers_main.cleanup_stale_sessions({})

    assert result == {"expired_pending": 1, "expired_in_progress": 1}
    assert ("update_status", stale_pending.id, SessionStatus.EXPIRED) in calls
    assert ("update_status", stale_progress.id, SessionStatus.EXPIRED) in calls
    assert any(
        c[0] == "update_attr" and c[1] == stale_pending.id and c[2][0] == "end_reason"
        for c in calls
    )
    assert any(
        c[0] == "update_attr" and c[1] == stale_progress.id and c[2][0] == "end_reason"
        for c in calls
    )
