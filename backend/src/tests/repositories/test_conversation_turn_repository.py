"""Unit tests for ConversationTurnRepository."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from src.models.conversation_turn_model import ConversationTurnDb
from src.models.domain_enums import ConversationSpeaker
from src.repository.conversation_turn_repository import ConversationTurnRepository


@pytest.mark.asyncio
async def test_find_by_session_id_returns_ordered_turns(
    async_session_mock: AsyncMock,
    execute_result_builder,
    session_factory,
):
    session_id = uuid.uuid4()
    t1 = ConversationTurnDb(
        session_id=session_id,
        turn_index=1,
        speaker=ConversationSpeaker.SUITOR,
        content="hello",
    )
    t2 = ConversationTurnDb(
        session_id=session_id,
        turn_index=2,
        speaker=ConversationSpeaker.AVATAR,
        content="hi",
    )
    async_session_mock.execute.return_value = execute_result_builder(
        all_values=[t1, t2]
    )

    repo = ConversationTurnRepository(session_factory=session_factory)
    result = await repo.find_by_session_id(session_id)

    assert result == [t1, t2]
