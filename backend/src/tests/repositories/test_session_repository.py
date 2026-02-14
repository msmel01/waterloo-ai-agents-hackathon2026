"""Unit tests for SessionRepository."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from src.models.domain_enums import SessionStatus
from src.models.session_model import SessionDb
from src.repository.session_repository import SessionRepository


@pytest.mark.asyncio
async def test_find_by_heart_id_returns_sessions(
    async_session_mock: AsyncMock,
    execute_result_builder,
    session_factory,
):
    heart_id = uuid.uuid4()
    s1 = SessionDb(heart_id=heart_id, suitor_id=uuid.uuid4())
    s2 = SessionDb(heart_id=heart_id, suitor_id=uuid.uuid4())
    async_session_mock.execute.return_value = execute_result_builder(
        all_values=[s1, s2]
    )

    repo = SessionRepository(session_factory=session_factory)
    result = await repo.find_by_heart_id(heart_id)

    assert result == [s1, s2]


@pytest.mark.asyncio
async def test_update_status_updates_and_returns_session(
    async_session_mock: AsyncMock,
    session_factory,
):
    session_id = uuid.uuid4()
    db_obj = SessionDb(id=session_id, heart_id=uuid.uuid4(), suitor_id=uuid.uuid4())
    async_session_mock.get.return_value = db_obj

    repo = SessionRepository(session_factory=session_factory)
    result = await repo.update_status(session_id, SessionStatus.IN_PROGRESS)

    assert result == db_obj
    assert db_obj.status == SessionStatus.IN_PROGRESS
    async_session_mock.commit.assert_awaited_once()
    async_session_mock.refresh.assert_awaited_once_with(db_obj)


@pytest.mark.asyncio
async def test_update_status_returns_none_when_missing(
    async_session_mock: AsyncMock,
    session_factory,
):
    async_session_mock.get.return_value = None

    repo = SessionRepository(session_factory=session_factory)
    result = await repo.update_status(uuid.uuid4(), SessionStatus.COMPLETED)

    assert result is None
    async_session_mock.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_find_active_by_suitor_returns_first_active(
    async_session_mock: AsyncMock,
    execute_result_builder,
    session_factory,
):
    suitor_id = uuid.uuid4()
    active = SessionDb(heart_id=uuid.uuid4(), suitor_id=suitor_id)
    async_session_mock.execute.return_value = execute_result_builder(first_value=active)

    repo = SessionRepository(session_factory=session_factory)
    result = await repo.find_active_by_suitor(suitor_id)

    assert result == active


@pytest.mark.asyncio
async def test_count_today_by_suitor_returns_int(
    async_session_mock: AsyncMock,
    session_factory,
):
    execute_result = Mock()
    execute_result.scalar_one_or_none.return_value = 2
    async_session_mock.execute.return_value = execute_result

    repo = SessionRepository(session_factory=session_factory)
    result = await repo.count_today_by_suitor(uuid.uuid4())

    assert result == 2


@pytest.mark.asyncio
async def test_find_by_suitor_returns_recent_sessions(
    async_session_mock: AsyncMock,
    execute_result_builder,
    session_factory,
):
    suitor_id = uuid.uuid4()
    s1 = SessionDb(heart_id=uuid.uuid4(), suitor_id=suitor_id)
    s2 = SessionDb(heart_id=uuid.uuid4(), suitor_id=suitor_id)
    async_session_mock.execute.return_value = execute_result_builder(
        all_values=[s1, s2]
    )

    repo = SessionRepository(session_factory=session_factory)
    result = await repo.find_by_suitor(suitor_id, limit=20)

    assert result == [s1, s2]


@pytest.mark.asyncio
async def test_find_stale_pending_returns_pending_sessions(
    async_session_mock: AsyncMock,
    execute_result_builder,
    session_factory,
):
    stale = SessionDb(
        heart_id=uuid.uuid4(),
        suitor_id=uuid.uuid4(),
        status=SessionStatus.PENDING,
    )
    async_session_mock.execute.return_value = execute_result_builder(all_values=[stale])

    repo = SessionRepository(session_factory=session_factory)
    result = await repo.find_stale_pending(datetime.now(timezone.utc))

    assert result == [stale]


@pytest.mark.asyncio
async def test_find_stale_in_progress_returns_stale_sessions(
    async_session_mock: AsyncMock,
    execute_result_builder,
    session_factory,
):
    stale = SessionDb(
        heart_id=uuid.uuid4(),
        suitor_id=uuid.uuid4(),
        status=SessionStatus.IN_PROGRESS,
        started_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    async_session_mock.execute.return_value = execute_result_builder(all_values=[stale])

    repo = SessionRepository(session_factory=session_factory)
    result = await repo.find_stale_in_progress(datetime.now(timezone.utc))

    assert result == [stale]
