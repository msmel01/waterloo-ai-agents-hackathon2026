"""Tests for M7 dashboard auth dependency."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.dependencies import verify_dashboard_access


@pytest.mark.asyncio
async def test_dashboard_key_rejected(monkeypatch):
    monkeypatch.setattr("src.dependencies.config.DASHBOARD_API_KEY", "expected-key")
    with pytest.raises(HTTPException) as exc:
        await verify_dashboard_access("bad-key")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_key_accepted(monkeypatch):
    monkeypatch.setattr("src.dependencies.config.DASHBOARD_API_KEY", "expected-key")
    out = await verify_dashboard_access("expected-key")
    assert out == "expected-key"
