from __future__ import annotations

import pytest

from src.api.v1.endpoints.dashboard import get_dashboard_stats
from src.models.domain_enums import SessionStatus, Verdict


def _build_stats_db(
    make_fake_db_m7,
    fake_result_builder_m7,
    *,
    total_suitors=0,
    status_rows=None,
    verdict_rows=None,
    avg_row=None,
    tier_rows=None,
    sessions_today=0,
    sessions_week=0,
    sessions_month=0,
    booking_total=0,
    booking_upcoming=0,
    heart=None,
):
    status_rows = status_rows or []
    verdict_rows = verdict_rows or []
    avg_row = avg_row or (0, 0, 0, 0, 0)
    tier_rows = tier_rows or []

    results = [
        fake_result_builder_m7(scalar_value=total_suitors),
        fake_result_builder_m7(all_values=status_rows),
        fake_result_builder_m7(all_values=verdict_rows),
        fake_result_builder_m7(one_value=avg_row),
        fake_result_builder_m7(all_values=tier_rows),
        fake_result_builder_m7(scalar_value=sessions_today),
        fake_result_builder_m7(scalar_value=sessions_week),
        fake_result_builder_m7(scalar_value=sessions_month),
        fake_result_builder_m7(scalar_value=booking_total),
        fake_result_builder_m7(scalar_value=booking_upcoming),
    ]
    return make_fake_db_m7(results, heart=heart)


@pytest.mark.asyncio
async def test_m7_stats_001_returns_200_with_valid_auth(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_stats_db(make_fake_db_m7, fake_result_builder_m7, heart=m7_seeded_heart)
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.total_sessions == 0


@pytest.mark.asyncio
async def test_m7_stats_002_response_shape(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_stats_db(make_fake_db_m7, fake_result_builder_m7, heart=m7_seeded_heart)
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    payload = out.model_dump()
    for key in [
        "total_suitors",
        "total_sessions",
        "completed_sessions",
        "active_sessions",
        "failed_sessions",
        "total_dates",
        "total_rejections",
        "match_rate",
        "avg_scores",
        "score_distribution",
        "recent_activity",
        "bookings",
    ]:
        assert key in payload


@pytest.mark.asyncio
async def test_m7_stats_003_empty_database_returns_zeros(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_stats_db(make_fake_db_m7, fake_result_builder_m7, heart=m7_seeded_heart)
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.total_suitors == 0
    assert out.total_sessions == 0
    assert out.match_rate == 0
    assert out.avg_scores.aggregate == 0


@pytest.mark.asyncio
async def test_m7_stats_004_total_suitors_count(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_stats_db(
        make_fake_db_m7, fake_result_builder_m7, total_suitors=5, heart=m7_seeded_heart
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.total_suitors == 5


@pytest.mark.asyncio
async def test_m7_stats_005_session_counts_by_status(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    status_rows = [
        (SessionStatus.COMPLETED, 3),
        (SessionStatus.IN_PROGRESS, 2),
        (SessionStatus.FAILED, 1),
        (SessionStatus.PENDING, 1),
    ]
    db = _build_stats_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        status_rows=status_rows,
        heart=m7_seeded_heart,
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.total_sessions == 7
    assert out.completed_sessions == 3
    assert out.active_sessions == 3
    assert out.failed_sessions == 1


@pytest.mark.asyncio
async def test_m7_stats_006_verdict_counts(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    verdict_rows = [(Verdict.DATE, 2), (Verdict.NO_DATE, 2)]
    db = _build_stats_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        verdict_rows=verdict_rows,
        heart=m7_seeded_heart,
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.total_dates == 2
    assert out.total_rejections == 2


@pytest.mark.asyncio
async def test_m7_stats_007_match_rate_calculation(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    status_rows = [(SessionStatus.COMPLETED, 10)]
    verdict_rows = [(Verdict.DATE, 4), (Verdict.NO_DATE, 6)]
    db = _build_stats_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        status_rows=status_rows,
        verdict_rows=verdict_rows,
        heart=m7_seeded_heart,
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.match_rate == 40.0


@pytest.mark.asyncio
async def test_m7_stats_008_match_rate_zero_when_no_completed(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    status_rows = [(SessionStatus.PENDING, 2)]
    verdict_rows = [(Verdict.DATE, 1)]
    db = _build_stats_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        status_rows=status_rows,
        verdict_rows=verdict_rows,
        heart=m7_seeded_heart,
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.match_rate == 0


@pytest.mark.asyncio
async def test_m7_stats_009_match_rate_100_when_all_dates(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    status_rows = [(SessionStatus.COMPLETED, 3)]
    verdict_rows = [(Verdict.DATE, 3)]
    db = _build_stats_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        status_rows=status_rows,
        verdict_rows=verdict_rows,
        heart=m7_seeded_heart,
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.match_rate == 100.0


@pytest.mark.asyncio
async def test_m7_stats_010_avg_scores_calculation(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    avg_row = (76.666, 70.0, 80.0, 70.0, 74.333)
    db = _build_stats_db(
        make_fake_db_m7, fake_result_builder_m7, avg_row=avg_row, heart=m7_seeded_heart
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.avg_scores.effort == pytest.approx(76.7, abs=0.1)
    assert out.avg_scores.aggregate == pytest.approx(74.3, abs=0.1)


@pytest.mark.asyncio
async def test_m7_stats_011_avg_scores_null_when_no_scores(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_stats_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        avg_row=(None, None, None, None, None),
        heart=m7_seeded_heart,
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.avg_scores.effort == 0
    assert out.avg_scores.aggregate == 0


@pytest.mark.asyncio
async def test_m7_stats_012_score_distribution_buckets(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    tier_rows = [("excellent", 2), ("good", 3), ("average", 1), ("below_average", 2)]
    db = _build_stats_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        tier_rows=tier_rows,
        heart=m7_seeded_heart,
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.score_distribution.excellent == 2
    assert out.score_distribution.good == 3
    assert out.score_distribution.average == 1
    assert out.score_distribution.below_average == 2


@pytest.mark.asyncio
async def test_m7_stats_013_score_distribution_boundary_values(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    tier_rows = [("excellent", 1), ("good", 1), ("average", 1), ("below_average", 1)]
    db = _build_stats_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        tier_rows=tier_rows,
        heart=m7_seeded_heart,
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.score_distribution.model_dump() == {
        "excellent": 1,
        "good": 1,
        "average": 1,
        "below_average": 1,
    }


@pytest.mark.asyncio
async def test_m7_stats_014_sessions_today_count(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_stats_db(
        make_fake_db_m7, fake_result_builder_m7, sessions_today=3, heart=m7_seeded_heart
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.recent_activity.sessions_today == 3


@pytest.mark.asyncio
async def test_m7_stats_015_sessions_this_week_count(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_stats_db(
        make_fake_db_m7, fake_result_builder_m7, sessions_week=12, heart=m7_seeded_heart
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.recent_activity.sessions_this_week == 12


@pytest.mark.asyncio
async def test_m7_stats_016_sessions_this_month_count(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_stats_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        sessions_month=34,
        heart=m7_seeded_heart,
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.recent_activity.sessions_this_month == 34


@pytest.mark.asyncio
async def test_m7_stats_017_booking_counts(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_stats_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        booking_total=3,
        booking_upcoming=2,
        heart=m7_seeded_heart,
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.bookings.total_booked == 3
    assert out.bookings.upcoming == 2


@pytest.mark.asyncio
async def test_m7_stats_018_booking_rate_calculation(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    status_rows = [(SessionStatus.COMPLETED, 8)]
    verdict_rows = [(Verdict.DATE, 8)]
    db = _build_stats_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        status_rows=status_rows,
        verdict_rows=verdict_rows,
        booking_total=6,
        heart=m7_seeded_heart,
    )
    out = await get_dashboard_stats(dashboard_request, "ok", db)
    assert out.bookings.booking_rate == 75.0
