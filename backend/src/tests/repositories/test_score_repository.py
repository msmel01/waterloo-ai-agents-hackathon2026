"""Unit tests for ScoreRepository."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from src.models.domain_enums import Verdict
from src.models.score_model import ScoreDb
from src.repository.score_repository import ScoreRepository


@pytest.mark.asyncio
async def test_find_by_session_id_returns_score(
    async_session_mock: AsyncMock,
    execute_result_builder,
    session_factory,
):
    session_id = uuid.uuid4()
    score = ScoreDb(
        session_id=session_id,
        effort_score=80,
        creativity_score=70,
        intent_clarity_score=90,
        emotional_intelligence_score=85,
        weighted_total=82.75,
        verdict=Verdict.DATE,
        feedback_text="Good effort",
    )
    async_session_mock.execute.return_value = execute_result_builder(first_value=score)

    repo = ScoreRepository(session_factory=session_factory)
    result = await repo.find_by_session_id(session_id)

    assert result == score
