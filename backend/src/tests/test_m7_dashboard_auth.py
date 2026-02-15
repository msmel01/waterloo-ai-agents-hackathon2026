from __future__ import annotations

import uuid

import pytest

from src.core.config import config
from src.dependencies import verify_dashboard_access
from src.main import app

VALID_DASHBOARD_KEY = "test-dashboard-key-12345"


@pytest.fixture(autouse=True)
def _dashboard_key(monkeypatch):
    monkeypatch.setattr(config, "DASHBOARD_API_KEY", VALID_DASHBOARD_KEY)


@pytest.mark.asyncio
async def test_m7_auth_001_valid_key_allows_access():
    out = await verify_dashboard_access(VALID_DASHBOARD_KEY)
    assert out == VALID_DASHBOARD_KEY


@pytest.mark.asyncio
async def test_m7_auth_002_invalid_key_rejected(client):
    resp = await client.get(
        "/api/v1/dashboard/stats", headers={"X-Dashboard-Key": "wrong-key"}
    )
    assert resp.status_code == 401
    assert resp.json().get("detail") == "Unauthorized"


@pytest.mark.asyncio
async def test_m7_auth_003_missing_key_rejected(client):
    resp = await client.get("/api/v1/dashboard/stats")
    assert resp.status_code in {401, 422}


@pytest.mark.asyncio
async def test_m7_auth_004_empty_key_rejected(client):
    resp = await client.get("/api/v1/dashboard/stats", headers={"X-Dashboard-Key": ""})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_m7_auth_005_auth_applies_to_all_dashboard_endpoints(client):
    session_id = str(uuid.uuid4())
    paths = [
        "/api/v1/dashboard/stats",
        "/api/v1/dashboard/sessions",
        f"/api/v1/dashboard/sessions/{session_id}",
        "/api/v1/dashboard/heart/status",
        "/api/v1/dashboard/stats/trends",
    ]
    for path in paths:
        resp = await client.get(path)
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_m7_auth_006_auth_does_not_affect_public_endpoints(client):
    route = next(
        r for r in app.routes if getattr(r, "path", None) == "/api/v1/public/{slug}"
    )
    deps = [getattr(dep.call, "__name__", "") for dep in route.dependant.dependencies]
    assert "verify_dashboard_access" not in deps


@pytest.mark.asyncio
async def test_m7_auth_007_auth_does_not_affect_suitor_endpoints(client):
    route = next(
        r for r in app.routes if getattr(r, "path", None) == "/api/v1/suitors/register"
    )
    deps = [getattr(dep.call, "__name__", "") for dep in route.dependant.dependencies]
    assert "verify_dashboard_access" not in deps


@pytest.mark.asyncio
async def test_m7_auth_008_key_is_case_sensitive(client):
    resp = await client.get(
        "/api/v1/dashboard/stats",
        headers={"X-Dashboard-Key": VALID_DASHBOARD_KEY.upper()},
    )
    assert resp.status_code == 401
