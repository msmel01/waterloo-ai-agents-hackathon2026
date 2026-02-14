"""Unit tests for ScreeningQuestionRepository."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from src.models.screening_question_model import ScreeningQuestionDb
from src.repository.screening_question_repository import ScreeningQuestionRepository


@pytest.mark.asyncio
async def test_find_by_heart_id_returns_list(
    async_session_mock: AsyncMock,
    execute_result_builder,
    session_factory,
):
    heart_id = uuid.uuid4()
    q1 = ScreeningQuestionDb(heart_id=heart_id, question_text="Q1", order_index=1)
    q2 = ScreeningQuestionDb(heart_id=heart_id, question_text="Q2", order_index=2)
    async_session_mock.execute.return_value = execute_result_builder(
        all_values=[q1, q2]
    )

    repo = ScreeningQuestionRepository(session_factory=session_factory)
    result = await repo.find_by_heart_id(heart_id)

    assert result == [q1, q2]


@pytest.mark.asyncio
async def test_bulk_reorder_updates_matching_items_and_returns_latest(
    async_session_mock: AsyncMock,
    execute_result_builder,
    session_factory,
    monkeypatch,
):
    heart_id = uuid.uuid4()
    q1 = ScreeningQuestionDb(
        id=uuid.uuid4(), heart_id=heart_id, question_text="Q1", order_index=1
    )
    q2 = ScreeningQuestionDb(
        id=uuid.uuid4(), heart_id=heart_id, question_text="Q2", order_index=2
    )
    async_session_mock.execute.return_value = execute_result_builder(
        all_values=[q1, q2]
    )

    repo = ScreeningQuestionRepository(session_factory=session_factory)

    reordered = [q2, q1]

    async def _fake_find_by_heart_id(_heart_id):
        return reordered

    monkeypatch.setattr(repo, "find_by_heart_id", _fake_find_by_heart_id)

    result = await repo.bulk_reorder(
        heart_id, [(q1.id, 5), (q2.id, 3), (uuid.uuid4(), 7)]
    )

    assert q1.order_index == 5
    assert q2.order_index == 3
    assert result == reordered
    assert async_session_mock.add.call_count == 2
    async_session_mock.commit.assert_awaited_once()
