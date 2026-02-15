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
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from httpx import ASGITransport

# Ensure required settings exist during test collection before src.core.config imports.
os.environ.setdefault("CLERK_JWKS_URL", "https://example.com/.well-known/jwks.json")
os.environ.setdefault("CLERK_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("CLERK_WEBHOOK_SECRET", "whsec_dummy")
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "5432")
os.environ.setdefault("DB_NAME", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test"
)
os.environ.setdefault("LIVEKIT_URL", "wss://example.livekit.cloud")
os.environ.setdefault("LIVEKIT_API_KEY", "lk_test_key")
os.environ.setdefault("LIVEKIT_API_SECRET", "lk_test_secret")
os.environ.setdefault("DEEPGRAM_API_KEY", "dg_test_key")
os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("ANTHROPIC_API_KEY", "anthropic-test")
os.environ.setdefault("CALCOM_API_KEY", "cal-test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


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


@pytest.fixture
async def db_session() -> AsyncMock:
    """Async SQLAlchemy session mock placeholder for integration-like tests."""
    session = AsyncMock()
    session.add = Mock()
    return session


@pytest.fixture
async def client():
    """Async HTTP client bound to FastAPI app with lifespan disabled."""
    from src.main import app

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as async_client:
        yield async_client


@pytest.fixture
def heart_config() -> dict[str, Any]:
    """Returns a valid heart_config dict for testing."""
    return {
        "name": "Test Heart",
        "slug": "test-heart",
        "persona": "A witty and warm person who loves deep conversations",
        "expectations": ["Sense of humor", "Emotional depth", "Creativity"],
        "screening_questions": [
            "What's the most thoughtful thing you've done for someone you care about?",
            "If we had one perfect day together, what would it look like?",
            "What's something you're passionate about that most people don't know?",
            "How do you handle disagreements in a relationship?",
            "What does love mean to you?",
        ],
        "cal_com": {"api_key": "test-cal-key", "event_type_id": 123456},
        "scoring": {
            "date_threshold": 65,
            "weights": {
                "effort": 0.30,
                "creativity": 0.20,
                "intent_clarity": 0.25,
                "emotional_intelligence": 0.25,
            },
        },
    }


@pytest.fixture
def sample_transcript() -> list[dict[str, Any]]:
    """Returns a realistic conversation transcript for scoring tests."""
    return [
        {
            "turn": 1,
            "question": "What's the most thoughtful thing you've done for someone?",
            "answer": "I once planned a surprise stargazing picnic for my partner's birthday...",
            "timestamp": "2026-02-14T20:01:00Z",
        },
        {
            "turn": 2,
            "question": "If we had one perfect day together, what would it look like?",
            "answer": "I'd start with making breakfast together, maybe trying a new recipe...",
            "timestamp": "2026-02-14T20:03:30Z",
        },
        {
            "turn": 3,
            "question": "What's something you're passionate about?",
            "answer": "I'm really into urban gardening. I've been growing vegetables on my balcony...",
            "timestamp": "2026-02-14T20:06:00Z",
        },
        {
            "turn": 4,
            "question": "How do you handle disagreements?",
            "answer": "I try to listen first and understand the other person's perspective...",
            "timestamp": "2026-02-14T20:08:45Z",
        },
        {
            "turn": 5,
            "question": "What does love mean to you?",
            "answer": "To me, love is about choosing someone every day, even when it's hard...",
            "timestamp": "2026-02-14T20:11:30Z",
        },
    ]


@pytest.fixture
async def seeded_heart() -> Any:
    from src.models.heart_model import HeartDb

    return HeartDb(
        id=uuid.uuid4(),
        display_name="Test Heart",
        bio="Bio",
        shareable_slug="test-heart",
        persona={"traits": ["witty", "warm", "direct"]},
        expectations={"values": ["kindness"]},
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
async def registered_suitor() -> Any:
    from src.models.suitor_model import SuitorDb

    return SuitorDb(
        id=uuid.uuid4(),
        clerk_user_id="user_test_123",
        name="Test Suitor",
        email="test@example.com",
        age=25,
        gender="male",
        orientation="straight",
        intro_message="Hello there",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
async def completed_session(
    seeded_heart: Any,
    registered_suitor: Any,
    sample_transcript: list[dict[str, Any]],
) -> Any:
    from src.models.domain_enums import SessionStatus
    from src.models.session_model import SessionDb

    return SessionDb(
        id=uuid.uuid4(),
        heart_id=seeded_heart.id,
        suitor_id=registered_suitor.id,
        livekit_room_name=f"session-{uuid.uuid4()}",
        status=SessionStatus.COMPLETED,
        started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        ended_at=datetime.now(timezone.utc),
        turn_summaries={"turns": sample_transcript},
        has_verdict=False,
        verdict_status="pending",
    )


@pytest.fixture
def mock_livekit() -> AsyncMock:
    svc = AsyncMock()
    svc.create_room.return_value = {"name": "session-room", "sid": "RM_123"}
    svc.create_agent_dispatch.return_value = {
        "id": "AD_123",
        "agent_name": "valentine-interview-agent",
        "room": "session-room",
    }
    svc.generate_suitor_token = Mock(return_value="mock.livekit.jwt")
    return svc


@pytest.fixture
def mock_deepgram() -> AsyncMock:
    svc = AsyncMock()
    svc.transcribe.return_value = "mock transcript"
    svc.synthesize.return_value = b"mock-audio"
    return svc


@pytest.fixture
def mock_openai() -> AsyncMock:
    svc = AsyncMock()
    svc.complete.return_value = {"text": "mock llm response"}
    return svc


@pytest.fixture
def mock_claude() -> AsyncMock:
    svc = AsyncMock()
    svc.score.return_value = {
        "category_scores": {
            "effort": 80,
            "creativity": 75,
            "intent_clarity": 82,
            "emotional_intelligence": 78,
        },
        "feedback": {"summary": "Great conversation overall."},
    }
    return svc


@pytest.fixture
def mock_calcom() -> AsyncMock:
    svc = AsyncMock()
    svc.validate_connection.return_value = True
    svc.get_available_slots.return_value = [
        {"start": "2026-02-20T14:00:00Z", "end": "2026-02-20T14:30:00Z"}
    ]
    return svc
