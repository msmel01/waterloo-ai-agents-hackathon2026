"""Unit tests for stale session cleanup worker task."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src.models.domain_enums import SessionStatus
from src.models.session_model import SessionDb
from workers import main as workers_main


class _ScalarResult:
    def __init__(self, values):
        self._values = values

    def all(self):
        return self._values


class _ExecuteResult:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return _ScalarResult(self._values)


class _SessionContext:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_cleanup_stale_sessions_expires_pending_and_in_progress(monkeypatch):
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

    session = AsyncMock()
    session.add = Mock()
    session.execute.side_effect = [
        _ExecuteResult([stale_pending]),
        _ExecuteResult([stale_progress]),
    ]

    fake_db = SimpleNamespace(session=lambda: _SessionContext(session))

    monkeypatch.setattr(workers_main, "database", fake_db)
    monkeypatch.setattr(workers_main.config, "SESSION_PENDING_TIMEOUT", 300)
    monkeypatch.setattr(workers_main.config, "SESSION_MAX_DURATION", 1800)

    result = await workers_main.cleanup_stale_sessions({})

    assert result == {"expired_pending": 1, "expired_in_progress": 1}
    assert stale_pending.status == SessionStatus.EXPIRED
    assert stale_pending.end_reason == "connection_timeout"
    assert stale_progress.status == SessionStatus.EXPIRED
    assert stale_progress.end_reason == "max_duration_exceeded"
    session.commit.assert_awaited_once()
