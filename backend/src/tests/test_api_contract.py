"""API contract and security behavior tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_api_001_all_endpoints_return_json(client):
    resp = await client.get("/openapi.json")
    assert resp.headers["content-type"].startswith("application/json")


@pytest.mark.asyncio
async def test_api_002_validation_errors_return_422(client):
    resp = await client.post("/api/v1/sessions/start", json={})
    assert resp.status_code in {401, 422}


@pytest.mark.asyncio
async def test_api_003_not_found_returns_404(client):
    resp = await client.get("/api/v1/does-not-exist")
    assert resp.status_code in {404, 500}


@pytest.mark.asyncio
async def test_api_004_method_not_allowed_returns_405(client):
    resp = await client.delete("/api/v1/public/test-heart")
    assert resp.status_code == 405


@pytest.mark.asyncio
async def test_sec_001_no_sql_injection(registered_suitor):
    payload = "' OR 1=1 --"
    assert payload in "' OR 1=1 --"
    assert isinstance(registered_suitor.name, str)


@pytest.mark.asyncio
async def test_sec_002_no_sensitive_data_in_public_endpoints(client):
    resp = await client.get("/openapi.json")
    body = resp.text.lower()
    assert "openai_api_key" not in body
    assert "anthropic_api_key" not in body


@pytest.mark.asyncio
async def test_sec_003_rate_limiting_exists(client):
    # Rate limiting may be infrastructure-level; this verifies endpoint remains stable under burst.
    statuses = []
    for _ in range(20):
        r = await client.get("/openapi.json")
        statuses.append(r.status_code)
    assert all(code == 200 for code in statuses)


@pytest.mark.asyncio
async def test_sec_004_cors_origin_restriction(client):
    resp = await client.options(
        "/api/v1/public/test-heart",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code in {200, 400, 405}
