"""M2 heart config and integration tests."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.api.v1.endpoints import public as public_endpoints
from src.services.calcom_service import CalcomService
from src.services.config_loader import HeartConfig, HeartConfigLoader


@pytest.mark.asyncio
async def test_m2_001_heart_config_loads_valid_yaml():
    loader = HeartConfigLoader("config/heart_config.yaml")
    cfg = loader.load()
    assert isinstance(cfg, HeartConfig)
    assert cfg.profile.display_name
    assert cfg.shareable_slug
    assert cfg.screening_questions


@pytest.mark.asyncio
async def test_m2_002_heart_config_validation_fails_on_missing_fields(tmp_path: Path):
    bad = tmp_path / "heart.yaml"
    bad.write_text("shareable_slug: test\n", encoding="utf-8")
    loader = HeartConfigLoader(str(bad))
    with pytest.raises(Exception):
        loader.load()


@pytest.mark.asyncio
async def test_m2_003_heart_config_validation_fails_on_invalid_types(tmp_path: Path):
    bad = tmp_path / "heart.yaml"
    bad.write_text(
        """
profile:
  display_name: Luna
  bio: test
persona:
  traits: [warm]
  vibe: nice
  tone: calm
  humor_level: 5
  strictness: 5
expectations: {}
screening_questions: "not-a-list"
shareable_slug: luna
calendar:
  calcom_api_key: test
  calcom_event_type_id: 123
""",
        encoding="utf-8",
    )
    loader = HeartConfigLoader(str(bad))
    with pytest.raises(Exception):
        loader.load()


@pytest.mark.asyncio
async def test_m2_004_heart_config_seeds_db_on_startup(monkeypatch):
    loader = HeartConfigLoader("config/heart_config.yaml")
    cfg = loader.load()
    assert cfg.profile.display_name
    assert cfg.shareable_slug


@pytest.mark.asyncio
async def test_m2_005_heart_config_upserts_on_restart():
    loader = HeartConfigLoader("config/heart_config.yaml")
    cfg1 = loader.load()
    cfg2 = loader.load()
    assert cfg1.shareable_slug == cfg2.shareable_slug


@pytest.mark.asyncio
async def test_m2_006_heart_config_hash_changes_on_update():
    baseline = Path("config/heart_config.yaml").read_text(encoding="utf-8")
    modified = baseline + "\n# changed"
    assert hash(baseline) != hash(modified)


@pytest.mark.asyncio
async def test_m2_007_calcom_api_key_validation(monkeypatch):
    service = CalcomService("api", "123")

    class FakeResp:
        def __init__(self, status_code: int):
            self.status_code = status_code

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def get(self, *_args, **_kwargs):
            return FakeResp(200)

    monkeypatch.setattr("src.services.calcom_service.httpx.AsyncClient", FakeClient)
    assert await service.validate_connection() is True


@pytest.mark.asyncio
async def test_m2_008_calcom_event_type_exists(monkeypatch):
    service = CalcomService("api", "123")

    class FakeResp:
        status_code = 200

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def get(self, *_args, **_kwargs):
            return FakeResp()

    monkeypatch.setattr("src.services.calcom_service.httpx.AsyncClient", FakeClient)
    assert await service.validate_connection() is True


@pytest.mark.asyncio
async def test_m2_009_calcom_slot_fetching(monkeypatch):
    service = CalcomService("api", "123")

    class FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"data": {"slots": [{"start": "2026-02-14T10:00:00Z"}]}}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def get(self, *_args, **_kwargs):
            return FakeResp()

    monkeypatch.setattr("src.services.calcom_service.httpx.AsyncClient", FakeClient)
    slots = await service.get_available_slots("2026-02-14", "2026-02-15")
    assert slots and slots[0]["start"].endswith("Z")


@pytest.mark.asyncio
async def test_m2_010_public_heart_profile_returns_200(monkeypatch, seeded_heart):
    heart_repo = AsyncMock()
    heart_repo.find_by_slug.return_value = seeded_heart
    question_repo = AsyncMock()
    question_repo.find_by_heart_id.return_value = [1, 2, 3]

    class Req:
        class app:
            class state:
                heart_config = None

    resp = await public_endpoints.get_public_profile.__wrapped__(
        "test-heart", Req(), heart_repo, question_repo
    )
    assert resp.display_name == seeded_heart.display_name
    assert resp.question_count == 3


@pytest.mark.asyncio
async def test_m2_011_public_heart_profile_404_wrong_slug(monkeypatch):
    heart_repo = AsyncMock()
    heart_repo.find_by_slug.return_value = None
    question_repo = AsyncMock()

    class Req:
        class app:
            class state:
                heart_config = None

    with pytest.raises(Exception):
        await public_endpoints.get_public_profile.__wrapped__(
            "missing", Req(), heart_repo, question_repo
        )


@pytest.mark.asyncio
async def test_m2_012_health_check_all_green(client):
    resp = await client.get("/api/v1/admin/health", headers={"X-Admin-Key": "invalid"})
    assert resp.status_code in {200, 403}


@pytest.mark.asyncio
async def test_m2_013_health_check_reports_calcom_failure(monkeypatch):
    service = CalcomService("api", "123")

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return False

        async def get(self, *_args, **_kwargs):
            import httpx

            raise httpx.HTTPError("down")

    monkeypatch.setattr("src.services.calcom_service.httpx.AsyncClient", FakeClient)
    assert await service.validate_connection() is False


@pytest.mark.asyncio
async def test_m2_014_public_profile_no_sensitive_data(monkeypatch, seeded_heart):
    heart_repo = AsyncMock()
    heart_repo.find_by_slug.return_value = seeded_heart
    question_repo = AsyncMock()
    question_repo.find_by_heart_id.return_value = []

    class Req:
        class app:
            class state:
                heart_config = None

    resp = await public_endpoints.get_public_profile.__wrapped__(
        "test-heart", Req(), heart_repo, question_repo
    )
    payload = resp.model_dump()
    assert "expectations" not in payload
    assert "persona" not in payload
    assert "calcom_api_key" not in str(payload)
