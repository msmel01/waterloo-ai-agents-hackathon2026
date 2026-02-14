"""Shared pytest fixtures for repository tests.

Fixture inventory:
- `session_ctx`: async context manager wrapper for AsyncSession-like mocks.
- `session_factory_builder`: builds a `session_factory` that yields one or more sessions.
- `execute_result_builder`: creates SQLAlchemy-like execute results (`scalars().first/all`).
- `async_session_mock`: default AsyncMock session for simple tests.
- `session_factory`: default factory that yields `async_session_mock`.
- `uuid4_str`: deterministic UUID string helper.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable
from unittest.mock import AsyncMock, Mock

import pytest

# Ensure required settings exist during test collection before src.core.config imports.
os.environ.setdefault("CLERK_JWKS_URL", "https://example.com/.well-known/jwks.json")
os.environ.setdefault("CLERK_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("CLERK_WEBHOOK_SECRET", "whsec_dummy")


@dataclass
class _ScalarResult:
    """Minimal scalar result shim for repository tests."""

    first_value: Any = None
    all_values: list[Any] | None = None

    def first(self) -> Any:
        """Return first scalar result."""
        return self.first_value

    def all(self) -> list[Any]:
        """Return all scalar results."""
        return self.all_values or []


@dataclass
class _ExecuteResult:
    """Minimal execute result shim exposing `scalars()`."""

    first_value: Any = None
    all_values: list[Any] | None = None

    def scalars(self) -> _ScalarResult:
        """Return scalar adapter."""
        return _ScalarResult(first_value=self.first_value, all_values=self.all_values)


class _SessionContext:
    """Async context manager that yields a mock session."""

    def __init__(self, session: AsyncMock):
        self._session = session

    async def __aenter__(self) -> AsyncMock:
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        return False


@pytest.fixture
def session_ctx() -> type[_SessionContext]:
    """Provide async context class for wrapping session mocks."""
    return _SessionContext


@pytest.fixture
def execute_result_builder() -> Callable[[Any, list[Any] | None], _ExecuteResult]:
    """Build SQLAlchemy-like execute result objects."""

    def _build(
        first_value: Any = None, all_values: list[Any] | None = None
    ) -> _ExecuteResult:
        return _ExecuteResult(first_value=first_value, all_values=all_values)

    return _build


@pytest.fixture
def async_session_mock() -> AsyncMock:
    """Provide an AsyncMock that behaves like AsyncSession."""
    session = AsyncMock()
    # SQLAlchemy AsyncSession.add is synchronous.
    session.add = Mock()
    return session


@pytest.fixture
def session_factory_builder(
    session_ctx: type[_SessionContext],
) -> Callable[..., Callable[[], _SessionContext]]:
    """Create a session factory yielding sessions in sequence."""

    def _build(*sessions: AsyncMock) -> Callable[[], _SessionContext]:
        queue = list(sessions)

        def _factory() -> _SessionContext:
            if not queue:
                raise RuntimeError(
                    "No mock sessions left in session_factory_builder queue"
                )
            return session_ctx(queue.pop(0))

        return _factory

    return _build


@pytest.fixture
def session_factory(
    async_session_mock: AsyncMock,
    session_factory_builder: Callable[..., Callable[[], _SessionContext]],
) -> Callable[[], _SessionContext]:
    """Default single-session factory."""
    return session_factory_builder(async_session_mock)


@pytest.fixture
def uuid4_str() -> str:
    """Deterministic UUID string for convenient test payloads."""
    return "11111111-1111-1111-1111-111111111111"
