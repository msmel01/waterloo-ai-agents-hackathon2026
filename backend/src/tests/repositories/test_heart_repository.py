"""Unit tests for HeartRepository."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from src.models.heart_model import HeartDb
from src.repository.heart_repository import HeartRepository


@pytest.mark.asyncio
async def test_find_by_slug_returns_heart(
    async_session_mock: AsyncMock,
    execute_result_builder,
    session_factory,
):
    heart = HeartDb(
        clerk_user_id="clerk_1",
        email="heart@example.com",
        display_name="Heart",
        shareable_slug="heart-slug",
        persona={"traits": [], "vibe": "", "tone": "", "humor_level": 0},
        expectations={"dealbreakers": [], "green_flags": [], "must_haves": []},
    )
    async_session_mock.execute.return_value = execute_result_builder(first_value=heart)

    repo = HeartRepository(session_factory=session_factory)
    result = await repo.find_by_slug("heart-slug")

    assert result == heart
    async_session_mock.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_find_by_clerk_id_returns_none(
    async_session_mock: AsyncMock,
    execute_result_builder,
    session_factory,
):
    async_session_mock.execute.return_value = execute_result_builder(first_value=None)
    repo = HeartRepository(session_factory=session_factory)

    result = await repo.find_by_clerk_id("missing")

    assert result is None


@pytest.mark.asyncio
async def test_delete_by_clerk_id_executes_and_commits(
    async_session_mock: AsyncMock,
    session_factory,
):
    repo = HeartRepository(session_factory=session_factory)

    await repo.delete_by_clerk_id("clerk_1")

    async_session_mock.execute.assert_awaited_once()
    async_session_mock.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_read_by_id_with_uuid_pk_returns_record(
    async_session_mock: AsyncMock,
    execute_result_builder,
    session_factory,
):
    heart = HeartDb(
        id=uuid.uuid4(),
        clerk_user_id="clerk_1",
        email="heart@example.com",
        display_name="Heart",
        shareable_slug="heart-slug",
        persona={"traits": [], "vibe": "", "tone": "", "humor_level": 0},
        expectations={"dealbreakers": [], "green_flags": [], "must_haves": []},
    )
    async_session_mock.execute.return_value = execute_result_builder(first_value=heart)

    repo = HeartRepository(session_factory=session_factory)
    result = await repo.read_by_id(heart.id)

    assert result == heart
