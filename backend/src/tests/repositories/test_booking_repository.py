"""Unit tests for BookingRepository."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from src.models.booking_model import BookingDb
from src.models.domain_enums import BookingStatus
from src.repository.booking_repository import BookingRepository


@pytest.mark.asyncio
async def test_find_by_session_id_returns_booking(
    async_session_mock: AsyncMock,
    execute_result_builder,
    session_factory,
):
    session_id = uuid.uuid4()
    booking = BookingDb(
        session_id=session_id,
        heart_id=uuid.uuid4(),
        suitor_id=uuid.uuid4(),
        calcom_booking_id="cal_123",
        scheduled_at=datetime.now(timezone.utc),
        status=BookingStatus.CONFIRMED,
    )
    async_session_mock.execute.return_value = execute_result_builder(
        first_value=booking
    )

    repo = BookingRepository(session_factory=session_factory)
    result = await repo.find_by_session_id(session_id)

    assert result == booking
