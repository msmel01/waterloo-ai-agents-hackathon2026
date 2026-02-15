from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.api.v1.endpoints.dashboard import get_dashboard_trends


def _trend_row(day: datetime, sessions: int, avg: float, dates: int, rejects: int):
    return SimpleNamespace(
        bucket=day,
        sessions=sessions,
        avg_aggregate=avg,
        dates=dates,
        rejections=rejects,
    )


def _build_trends_db(make_fake_db_m7, fake_result_builder_m7, rows, *, heart):
    return make_fake_db_m7([fake_result_builder_m7(all_values=rows)], heart=heart)


async def _call_trends(func, request, auth, db, **kwargs):
    defaults = {"period": "daily", "days": 30}
    defaults.update(kwargs)
    return await func(
        request,
        auth,
        db,
        period=defaults["period"],
        days=defaults["days"],
    )


@pytest.mark.asyncio
async def test_m7_trends_001_returns_daily_data(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    now = datetime.now(timezone.utc)
    rows = [_trend_row(now - timedelta(days=i), 1, 70.0 + i, 1, 0) for i in range(5)]
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_trends_db(
        make_fake_db_m7, fake_result_builder_m7, rows, heart=m7_seeded_heart
    )
    out = await _call_trends(get_dashboard_trends, dashboard_request, "ok", db)
    assert out.period == "daily"
    assert len(out.data) == 5


@pytest.mark.asyncio
async def test_m7_trends_002_response_item_shape(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    now = datetime.now(timezone.utc)
    rows = [_trend_row(now, 2, 65.0, 1, 1)]
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_trends_db(
        make_fake_db_m7, fake_result_builder_m7, rows, heart=m7_seeded_heart
    )
    out = await _call_trends(get_dashboard_trends, dashboard_request, "ok", db)
    point = out.data[0].model_dump()
    for key in ["date", "sessions", "avg_aggregate", "dates", "rejections"]:
        assert key in point


@pytest.mark.asyncio
async def test_m7_trends_003_daily_aggregation_correct(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    day = datetime(2026, 2, 14, tzinfo=timezone.utc)
    rows = [_trend_row(day, 3, 70.0, 2, 1)]
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_trends_db(
        make_fake_db_m7, fake_result_builder_m7, rows, heart=m7_seeded_heart
    )
    out = await _call_trends(get_dashboard_trends, dashboard_request, "ok", db)
    assert out.data[0].sessions == 3
    assert out.data[0].dates == 2
    assert out.data[0].rejections == 1
    assert out.data[0].avg_aggregate == pytest.approx(70.0)


@pytest.mark.asyncio
async def test_m7_trends_004_weekly_period(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    now = datetime.now(timezone.utc)
    rows = [_trend_row(now, 4, 68.2, 2, 2)]
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_trends_db(
        make_fake_db_m7, fake_result_builder_m7, rows, heart=m7_seeded_heart
    )
    out = await _call_trends(
        get_dashboard_trends, dashboard_request, "ok", db, period="weekly"
    )
    assert out.period == "weekly"


@pytest.mark.asyncio
async def test_m7_trends_005_custom_days_range(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    now = datetime.now(timezone.utc)
    rows = [_trend_row(now - timedelta(days=2), 1, 80.0, 1, 0)]
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_trends_db(
        make_fake_db_m7, fake_result_builder_m7, rows, heart=m7_seeded_heart
    )
    out = await _call_trends(get_dashboard_trends, dashboard_request, "ok", db, days=7)
    assert len(out.data) == 1


@pytest.mark.asyncio
async def test_m7_trends_006_default_30_days(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    now = datetime.now(timezone.utc)
    rows = [_trend_row(now - timedelta(days=20), 2, 72.0, 1, 1)]
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_trends_db(
        make_fake_db_m7, fake_result_builder_m7, rows, heart=m7_seeded_heart
    )
    out = await _call_trends(get_dashboard_trends, dashboard_request, "ok", db)
    assert all(point.date for point in out.data)


@pytest.mark.asyncio
async def test_m7_trends_007_empty_days_excluded_or_zero(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    rows = [
        _trend_row(datetime(2026, 2, 10, tzinfo=timezone.utc), 1, 60.0, 0, 1),
        _trend_row(datetime(2026, 2, 14, tzinfo=timezone.utc), 2, 75.0, 1, 1),
    ]
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_trends_db(
        make_fake_db_m7, fake_result_builder_m7, rows, heart=m7_seeded_heart
    )
    out = await _call_trends(get_dashboard_trends, dashboard_request, "ok", db)
    assert len(out.data) in (2, 5)


@pytest.mark.asyncio
async def test_m7_trends_008_only_completed_sessions(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    day = datetime(2026, 2, 14, tzinfo=timezone.utc)
    rows = [_trend_row(day, 2, 70.0, 1, 1)]
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_trends_db(
        make_fake_db_m7, fake_result_builder_m7, rows, heart=m7_seeded_heart
    )
    out = await _call_trends(get_dashboard_trends, dashboard_request, "ok", db)
    assert out.data[0].sessions == 2


@pytest.mark.asyncio
async def test_m7_trends_009_sorted_by_date_descending(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    rows = [
        _trend_row(datetime(2026, 2, 14, tzinfo=timezone.utc), 1, 70.0, 1, 0),
        _trend_row(datetime(2026, 2, 13, tzinfo=timezone.utc), 1, 65.0, 0, 1),
    ]
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_trends_db(
        make_fake_db_m7, fake_result_builder_m7, rows, heart=m7_seeded_heart
    )
    out = await _call_trends(get_dashboard_trends, dashboard_request, "ok", db)
    dates = [point.date for point in out.data]
    assert dates == sorted(dates, reverse=True)


@pytest.mark.asyncio
async def test_m7_trends_010_invalid_period_rejected(
    client, dashboard_headers, monkeypatch
):
    from src.core import config as config_module

    monkeypatch.setattr(
        config_module.config,
        "DASHBOARD_API_KEY",
        dashboard_headers["X-Dashboard-Key"],
        raising=False,
    )
    resp = await client.get(
        "/api/v1/dashboard/stats/trends?period=hourly", headers=dashboard_headers
    )
    assert resp.status_code == 422
