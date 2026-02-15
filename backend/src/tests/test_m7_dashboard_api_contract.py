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
async def test_m7_api_001_all_dashboard_endpoints_return_json(
    client, dashboard_headers
):
    sid = str(uuid.uuid4())
    endpoints = [
        "/api/v1/dashboard/stats",
        "/api/v1/dashboard/sessions",
        f"/api/v1/dashboard/sessions/{sid}",
        "/api/v1/dashboard/heart/status",
        "/api/v1/dashboard/stats/trends",
    ]
    for path in endpoints:
        resp = await client.get(path, headers=dashboard_headers)
        assert "application/json" in resp.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_m7_api_002_stats_endpoint_methods(client, dashboard_headers):
    ok = await client.get("/api/v1/dashboard/stats", headers=dashboard_headers)
    post = await client.post("/api/v1/dashboard/stats", headers=dashboard_headers)
    delete = await client.delete("/api/v1/dashboard/stats", headers=dashboard_headers)
    assert ok.status_code in (200, 404)
    assert post.status_code == 405
    assert delete.status_code == 405


@pytest.mark.asyncio
async def test_m7_api_003_sessions_endpoint_methods(client, dashboard_headers):
    ok = await client.get("/api/v1/dashboard/sessions", headers=dashboard_headers)
    post = await client.post("/api/v1/dashboard/sessions", headers=dashboard_headers)
    put = await client.put("/api/v1/dashboard/sessions", headers=dashboard_headers)
    delete = await client.delete(
        "/api/v1/dashboard/sessions", headers=dashboard_headers
    )
    assert ok.status_code in (200, 404)
    assert post.status_code == 405
    assert put.status_code == 405
    assert delete.status_code == 405


@pytest.mark.asyncio
async def test_m7_api_004_detail_endpoint_methods(client, dashboard_headers):
    sid = str(uuid.uuid4())
    ok = await client.get(
        f"/api/v1/dashboard/sessions/{sid}", headers=dashboard_headers
    )
    post = await client.post(
        f"/api/v1/dashboard/sessions/{sid}", headers=dashboard_headers
    )
    put = await client.put(
        f"/api/v1/dashboard/sessions/{sid}", headers=dashboard_headers
    )
    delete = await client.delete(
        f"/api/v1/dashboard/sessions/{sid}", headers=dashboard_headers
    )
    assert ok.status_code in (200, 404)
    assert post.status_code == 405
    assert put.status_code == 405
    assert delete.status_code == 405


@pytest.mark.asyncio
async def test_m7_api_005_status_get_and_patch_only(client, dashboard_headers):
    ok_get = await client.get(
        "/api/v1/dashboard/heart/status", headers=dashboard_headers
    )
    ok_patch = await client.patch(
        "/api/v1/dashboard/heart/status",
        headers=dashboard_headers,
        json={"active": False},
    )
    post = await client.post(
        "/api/v1/dashboard/heart/status", headers=dashboard_headers
    )
    delete = await client.delete(
        "/api/v1/dashboard/heart/status", headers=dashboard_headers
    )
    assert ok_get.status_code in (200, 404)
    assert ok_patch.status_code in (200, 404)
    assert post.status_code == 405
    assert delete.status_code == 405


@pytest.mark.asyncio
async def test_m7_api_006_session_list_invalid_sort_by(client, dashboard_headers):
    resp = await client.get(
        "/api/v1/dashboard/sessions?sort_by=invalid_field", headers=dashboard_headers
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_m7_api_007_session_list_invalid_verdict_filter(
    client, dashboard_headers
):
    resp = await client.get(
        "/api/v1/dashboard/sessions?verdict=maybe", headers=dashboard_headers
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_m7_api_008_date_range_invalid_format(client, dashboard_headers):
    resp = await client.get(
        "/api/v1/dashboard/sessions?date_from=not-a-date", headers=dashboard_headers
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_m7_api_009_date_range_start_after_end(client, dashboard_headers):
    resp = await client.get(
        "/api/v1/dashboard/sessions?date_from=2026-02-20&date_to=2026-02-10",
        headers=dashboard_headers,
    )
    assert resp.status_code in (200, 422)


@pytest.mark.asyncio
async def test_m7_api_010_trends_negative_days(client, dashboard_headers):
    resp = await client.get(
        "/api/v1/dashboard/stats/trends?days=-5", headers=dashboard_headers
    )
    assert resp.status_code == 422
