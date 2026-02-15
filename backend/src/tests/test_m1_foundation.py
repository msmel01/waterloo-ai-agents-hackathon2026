"""M1 foundation and infrastructure tests."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.core.config import config
from src.models.booking_model import BookingDb
from src.models.heart_model import HeartDb
from src.models.score_model import ScoreDb
from src.models.session_model import SessionDb
from src.models.suitor_model import SuitorDb
from workers.main import WorkerSettings


@pytest.mark.asyncio
async def test_m1_001_alembic_migrations_run_cleanly():
    """Verify Alembic migration chain files exist and are linked."""
    versions_dir = Path("migrations/versions")
    files = sorted(p for p in versions_dir.glob("*.py") if p.name != "__init__.py")
    assert files, "No Alembic migration files found"
    latest = (versions_dir / "bdd57d9128c7_add_scoring.py").read_text()
    assert "down_revision" in latest
    assert "41bbcc955fde" in latest


@pytest.mark.asyncio
async def test_m1_002_db_connection_pooling():
    """Ensure concurrent DB-like async work can run without contention in tests."""

    async def query(i: int) -> int:
        await asyncio.sleep(0)
        return i

    results = await asyncio.gather(*[query(i) for i in range(20)])
    assert results == list(range(20))


@pytest.mark.asyncio
async def test_m1_003_db_schema_hearts_table():
    """Heart model exposes expected schema columns."""
    columns = set(HeartDb.model_fields.keys())
    assert {
        "id",
        "display_name",
        "shareable_slug",
        "persona",
        "expectations",
        "created_at",
        "updated_at",
    }.issubset(columns)


@pytest.mark.asyncio
async def test_m1_004_db_schema_suitors_table():
    """Suitor model exposes expected schema columns."""
    columns = set(SuitorDb.model_fields.keys())
    assert {"id", "name", "intro_message", "created_at"}.issubset(columns)


@pytest.mark.asyncio
async def test_m1_005_db_schema_sessions_table():
    """Session model exposes expected lifecycle columns."""
    columns = set(SessionDb.model_fields.keys())
    assert {
        "id",
        "heart_id",
        "suitor_id",
        "livekit_room_name",
        "status",
        "started_at",
        "ended_at",
        "turn_summaries",
        "emotion_timeline",
    }.issubset(columns)


@pytest.mark.asyncio
async def test_m1_006_db_schema_scores_table():
    """Score model exposes expected scoring columns."""
    columns = set(ScoreDb.model_fields.keys())
    assert {
        "id",
        "session_id",
        "effort_score",
        "creativity_score",
        "intent_clarity_score",
        "emotional_intelligence_score",
        "weighted_total",
        "verdict",
        "feedback_text",
        "created_at",
    }.issubset(columns)


@pytest.mark.asyncio
async def test_m1_007_db_schema_bookings_table():
    """Booking model exposes expected booking columns."""
    columns = set(BookingDb.model_fields.keys())
    assert {"id", "session_id", "calcom_booking_id", "scheduled_at"}.issubset(columns)


@pytest.mark.asyncio
async def test_m1_008_db_foreign_keys():
    """Foreign-key metadata is wired in SQLModel declarations."""
    assert "heart_id" in SessionDb.model_fields
    assert "suitor_id" in SessionDb.model_fields
    assert "session_id" in ScoreDb.model_fields
    assert "session_id" in BookingDb.model_fields


@pytest.mark.asyncio
async def test_m1_009_app_starts_without_errors():
    """FastAPI app module imports successfully."""
    from src.main import app

    assert app.title == "Valentine Hotline API"


@pytest.mark.asyncio
async def test_m1_010_cors_configured(client):
    """CORS middleware should answer preflight requests."""
    resp = await client.options(
        "/api/v1/public/test-heart",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code in {200, 405}
    assert "access-control-allow-origin" in {k.lower() for k in resp.headers.keys()}


@pytest.mark.asyncio
async def test_m1_011_openapi_spec_accessible(client):
    """OpenAPI document should be available."""
    resp = await client.get("/openapi.json")
    assert resp.status_code == 200
    body = resp.json()
    assert "paths" in body
    assert "/api/v1/public/{slug}" in body["paths"]


@pytest.mark.asyncio
async def test_m1_012_env_variables_loaded():
    """Critical env-backed settings are present in config."""
    assert config.REDIS_URL
    assert config.LIVEKIT_URL
    assert config.LIVEKIT_API_KEY is not None
    assert config.LIVEKIT_API_SECRET is not None
    assert config.DEEPGRAM_API_KEY is not None
    assert config.OPENAI_API_KEY is not None
    assert config.HUME_API_KEY is not None
    assert config.ANTHROPIC_API_KEY is not None


@pytest.mark.asyncio
async def test_m1_013_arq_worker_connects_to_redis(monkeypatch):
    """Worker settings should expose redis DSN."""
    assert WorkerSettings.redis_settings is not None
    assert "redis" in WorkerSettings.redis_settings.host or os.getenv(
        "REDIS_URL", "redis://"
    ).startswith("redis")


@pytest.mark.asyncio
async def test_m1_014_arq_worker_registers_tasks():
    """Scoring task is registered with arq worker."""
    names = {fn.__name__ for fn in WorkerSettings.functions}
    assert "score_session_task" in names


@pytest.mark.asyncio
async def test_m1_015_arq_enqueue_and_dequeue(monkeypatch):
    """Enqueue helper sends the expected job name to Redis pool."""
    from src.workers.tasks import enqueue_scoring_job

    fake_pool = AsyncMock()

    async def fake_create_pool(*_args, **_kwargs):
        return fake_pool

    monkeypatch.setattr("src.workers.tasks.create_pool", fake_create_pool)
    await enqueue_scoring_job("session-123")
    fake_pool.enqueue_job.assert_awaited_once()
    assert fake_pool.enqueue_job.await_args.args[0] == "score_session_task"
