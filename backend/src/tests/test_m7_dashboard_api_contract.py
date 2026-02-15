from __future__ import annotations

import uuid

import pytest


@pytest.fixture(autouse=True)
def _patch_dashboard_key(monkeypatch):
    from src.core import config as config_module

    monkeypatch.setattr(
        config_module.config,
        "DASHBOARD_API_KEY",
        "test-dashboard-key-12345",
        raising=False,
    )


@pytest.mark.asyncio
async def test_m7_api_001_all_dashboard_endpoints_return_json(client):
    sid = str(uuid.uuid4())
    endpoints = [
        "/api/v1/dashboard/stats",
        "/api/v1/dashboard/sessions",
        f"/api/v1/dashboard/sessions/{sid}",
        "/api/v1/dashboard/heart/status",
        "/api/v1/dashboard/stats/trends",
    ]
    for path in endpoints:
        resp = await client.get(path)
        assert "application/json" in resp.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_m7_api_002_stats_endpoint_methods(client):
    ok = await client.get("/api/v1/dashboard/stats")
    post = await client.post("/api/v1/dashboard/stats")
    delete = await client.delete("/api/v1/dashboard/stats")
    assert ok.status_code in (401, 422)
    assert post.status_code == 405
    assert delete.status_code == 405


@pytest.mark.asyncio
async def test_m7_api_003_sessions_endpoint_methods(client):
    ok = await client.get("/api/v1/dashboard/sessions")
    post = await client.post("/api/v1/dashboard/sessions")
    put = await client.put("/api/v1/dashboard/sessions")
    delete = await client.delete("/api/v1/dashboard/sessions")
    assert ok.status_code in (401, 422)
    assert post.status_code == 405
    assert put.status_code == 405
    assert delete.status_code == 405


@pytest.mark.asyncio
async def test_m7_api_004_detail_endpoint_methods(client):
    sid = str(uuid.uuid4())
    ok = await client.get(f"/api/v1/dashboard/sessions/{sid}")
    post = await client.post(f"/api/v1/dashboard/sessions/{sid}")
    put = await client.put(f"/api/v1/dashboard/sessions/{sid}")
    delete = await client.delete(f"/api/v1/dashboard/sessions/{sid}")
    assert ok.status_code in (401, 422)
    assert post.status_code == 405
    assert put.status_code == 405
    assert delete.status_code == 405


@pytest.mark.asyncio
async def test_m7_api_005_status_get_and_patch_only(client):
    ok_get = await client.get("/api/v1/dashboard/heart/status")
    ok_patch = await client.patch(
        "/api/v1/dashboard/heart/status", json={"active": False}
    )
    post = await client.post("/api/v1/dashboard/heart/status")
    delete = await client.delete("/api/v1/dashboard/heart/status")
    assert ok_get.status_code in (401, 422)
    assert ok_patch.status_code in (401, 422)
    assert post.status_code == 405
    assert delete.status_code == 405


@pytest.mark.asyncio
async def test_m7_api_006_session_list_invalid_sort_by(client):
    resp = await client.get("/api/v1/dashboard/sessions?sort_by=invalid_field")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_m7_api_007_session_list_invalid_verdict_filter(client):
    resp = await client.get("/api/v1/dashboard/sessions?verdict=maybe")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_m7_api_008_date_range_invalid_format(client):
    resp = await client.get("/api/v1/dashboard/sessions?date_from=not-a-date")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_m7_api_009_date_range_start_after_end(client):
    resp = await client.get(
        "/api/v1/dashboard/sessions?date_from=2026-02-20&date_to=2026-02-10",
    )
    assert resp.status_code in (401, 422)


@pytest.mark.asyncio
async def test_m7_api_010_trends_negative_days(client):
    resp = await client.get("/api/v1/dashboard/stats/trends?days=-5")
    assert resp.status_code == 422
