from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from src.api.v1.endpoints.dashboard import get_dashboard_sessions


def _rows_for_sessions(sessions, suitors, scores=None, booking=None):
    scores = scores or []
    score_map = {s.session_id: s for s in scores}
    rows = []
    for idx, session in enumerate(sessions):
        suitor = suitors[idx]
        score = score_map.get(session.id)
        agg = score.final_score if score else None
        row_booking = booking if booking and booking.session_id == session.id else None
        rows.append((session, suitor, score, row_booking, agg))
    return rows


def _build_db_for_sessions(
    make_fake_db_m7, fake_result_builder_m7, *, total, rows, heart
):
    return make_fake_db_m7(
        [
            fake_result_builder_m7(scalar_value=total),
            fake_result_builder_m7(all_values=rows),
        ],
        heart=heart,
    )


async def _call_sessions(func, request, auth, db, *args, **kwargs):
    defaults = {
        "page": 1,
        "per_page": 20,
        "verdict": None,
        "sort_by": "date",
        "sort_order": "desc",
        "search": None,
        "date_from": None,
        "date_to": None,
    }
    defaults.update(kwargs)
    return await func(
        request,
        auth,
        db,
        page=defaults["page"],
        per_page=defaults["per_page"],
        verdict=defaults["verdict"],
        sort_by=defaults["sort_by"],
        sort_order=defaults["sort_order"],
        search=defaults["search"],
        date_from=defaults["date_from"],
        date_to=defaults["date_to"],
    )


@pytest.mark.asyncio
async def test_m7_sessions_001_returns_paginated_list(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    m7_sample_scores,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions(m7_sample_sessions, m7_sample_suitors, m7_sample_scores)
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=5,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    assert len(out.sessions) == 5
    assert out.pagination.total == 5


@pytest.mark.asyncio
async def test_m7_sessions_002_response_item_shape(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions([m7_sample_sessions[0]], [m7_sample_suitors[0]])
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=1,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    item = out.sessions[0].model_dump()
    for key in [
        "session_id",
        "suitor_name",
        "suitor_intro",
        "started_at",
        "ended_at",
        "duration_seconds",
        "status",
        "questions_asked",
        "scores",
        "verdict",
        "has_booking",
        "booking_date",
    ]:
        assert key in item


@pytest.mark.asyncio
async def test_m7_sessions_003_empty_list(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_db_for_sessions(
        make_fake_db_m7, fake_result_builder_m7, total=0, rows=[], heart=m7_seeded_heart
    )
    out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    assert out.sessions == []
    assert out.pagination.total == 0


@pytest.mark.asyncio
async def test_m7_sessions_004_includes_suitor_data(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions([m7_sample_sessions[0]], [m7_sample_suitors[0]])
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=1,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    assert out.sessions[0].suitor_name == "Alex"
    assert out.sessions[0].suitor_intro == "Hey, I love hiking and cooking."


@pytest.mark.asyncio
async def test_m7_sessions_005_duration_calculated(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    sess = m7_sample_sessions[0]
    sess.started_at = datetime.now(timezone.utc)
    sess.ended_at = sess.started_at + timedelta(minutes=10)
    rows = _rows_for_sessions([sess], [m7_sample_suitors[0]])
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=1,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    assert out.sessions[0].duration_seconds == 600


@pytest.mark.asyncio
async def test_m7_sessions_006_duration_null_for_active_session(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    sess = m7_sample_sessions[3]
    sess.ended_at = None
    rows = _rows_for_sessions([sess], [m7_sample_suitors[3]])
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=1,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    assert out.sessions[0].duration_seconds is None


@pytest.mark.asyncio
async def test_m7_sessions_007_questions_asked_from_transcript(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions([m7_sample_sessions[0]], [m7_sample_suitors[0]])
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=1,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    assert out.sessions[0].questions_asked == 5


@pytest.mark.asyncio
async def test_m7_sessions_008_scores_null_for_unscored_session(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions([m7_sample_sessions[4]], [m7_sample_suitors[4]])
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=1,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    assert out.sessions[0].scores is None
    assert out.sessions[0].verdict == "pending"


@pytest.mark.asyncio
async def test_m7_sessions_009_has_booking_true_when_booked(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    m7_sample_scores,
    m7_sample_booking,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions(
        [m7_sample_sessions[0]],
        [m7_sample_suitors[0]],
        [m7_sample_scores[0]],
        m7_sample_booking,
    )
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=1,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    assert out.sessions[0].has_booking is True
    assert out.sessions[0].booking_date is not None


@pytest.mark.asyncio
async def test_m7_sessions_010_has_booking_false_when_no_booking(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    m7_sample_scores,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions(
        [m7_sample_sessions[2]], [m7_sample_suitors[2]], [m7_sample_scores[2]]
    )
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=1,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    assert out.sessions[0].has_booking is False
    assert out.sessions[0].booking_date is None


@pytest.mark.asyncio
async def test_m7_sessions_011_default_pagination(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions(m7_sample_sessions, m7_sample_suitors)
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=25,
        rows=rows[:20],
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    assert out.pagination.page == 1
    assert out.pagination.per_page == 20
    assert out.pagination.total == 25
    assert out.pagination.total_pages == 2


@pytest.mark.asyncio
async def test_m7_sessions_012_custom_page_size(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions(m7_sample_sessions, m7_sample_suitors)
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=15,
        rows=rows[:5],
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(
        get_dashboard_sessions, dashboard_request, "ok", db, page=2, per_page=5
    )
    assert len(out.sessions) == 5
    assert out.pagination.page == 2
    assert out.pagination.has_prev is True
    assert out.pagination.has_next is True


@pytest.mark.asyncio
async def test_m7_sessions_013_last_page(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions(m7_sample_sessions[:2], m7_sample_suitors[:2])
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=22,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(
        get_dashboard_sessions, dashboard_request, "ok", db, page=3, per_page=10
    )
    assert len(out.sessions) == 2
    assert out.pagination.has_next is False


@pytest.mark.asyncio
async def test_m7_sessions_014_max_per_page_enforced(client, dashboard_headers):
    resp = await client.get(
        "/api/v1/dashboard/sessions?per_page=200", headers=dashboard_headers
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_m7_sessions_015_page_zero_or_negative_rejected(
    client, dashboard_headers
):
    resp0 = await client.get(
        "/api/v1/dashboard/sessions?page=0", headers=dashboard_headers
    )
    respn = await client.get(
        "/api/v1/dashboard/sessions?page=-1", headers=dashboard_headers
    )
    assert resp0.status_code == 422
    assert respn.status_code == 422


@pytest.mark.asyncio
async def test_m7_sessions_016_filter_by_verdict_date(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    m7_sample_scores,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions(
        [m7_sample_sessions[0], m7_sample_sessions[2]],
        [m7_sample_suitors[0], m7_sample_suitors[2]],
        [m7_sample_scores[0], m7_sample_scores[2]],
    )
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=2,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(
        get_dashboard_sessions, dashboard_request, "ok", db, verdict="date"
    )
    assert len(out.sessions) == 2
    assert all(row.verdict == "date" for row in out.sessions)


@pytest.mark.asyncio
async def test_m7_sessions_017_filter_by_verdict_no_date(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    m7_sample_scores,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions(
        [m7_sample_sessions[1]], [m7_sample_suitors[1]], [m7_sample_scores[1]]
    )
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=1,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(
        get_dashboard_sessions, dashboard_request, "ok", db, verdict="no_date"
    )
    assert len(out.sessions) == 1
    assert out.sessions[0].verdict == "no_date"


@pytest.mark.asyncio
async def test_m7_sessions_018_filter_by_verdict_pending(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions([m7_sample_sessions[3]], [m7_sample_suitors[3]])
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=1,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(
        get_dashboard_sessions, dashboard_request, "ok", db, verdict="pending"
    )
    assert len(out.sessions) == 1
    assert out.sessions[0].verdict == "pending"


@pytest.mark.asyncio
async def test_m7_sessions_019_search_by_suitor_name(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    suitors = m7_sample_suitors[:2]
    suitors[1].name = "Alexandra"
    rows = _rows_for_sessions(m7_sample_sessions[:2], suitors)
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=2,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(
        get_dashboard_sessions, dashboard_request, "ok", db, search="alex"
    )
    assert {s.suitor_name for s in out.sessions} == {"Alex", "Alexandra"}


@pytest.mark.asyncio
async def test_m7_sessions_020_search_no_results(
    dashboard_request, m7_seeded_heart, make_fake_db_m7, fake_result_builder_m7
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_db_for_sessions(
        make_fake_db_m7, fake_result_builder_m7, total=0, rows=[], heart=m7_seeded_heart
    )
    out = await _call_sessions(
        get_dashboard_sessions, dashboard_request, "ok", db, search="nonexistentname"
    )
    assert out.sessions == []
    assert out.pagination.total == 0


@pytest.mark.asyncio
async def test_m7_sessions_021_filter_by_date_range(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions([m7_sample_sessions[1]], [m7_sample_suitors[1]])
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=1,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(
        get_dashboard_sessions,
        dashboard_request,
        "ok",
        db,
        date_from=date(2026, 2, 11),
        date_to=date(2026, 2, 13),
    )
    assert len(out.sessions) == 1


@pytest.mark.asyncio
async def test_m7_sessions_022_combined_filters(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    m7_sample_scores,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions(
        [m7_sample_sessions[0]], [m7_sample_suitors[0]], [m7_sample_scores[0]]
    )
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=1,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(
        get_dashboard_sessions,
        dashboard_request,
        "ok",
        db,
        verdict="date",
        search="al",
        sort_by="score",
        sort_order="desc",
    )
    assert len(out.sessions) == 1
    assert out.sessions[0].suitor_name == "Alex"


@pytest.mark.asyncio
async def test_m7_sessions_023_sort_by_date_desc_default(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions(m7_sample_sessions[:3], m7_sample_suitors[:3])
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=3,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    assert out.pagination.page == 1


@pytest.mark.asyncio
async def test_m7_sessions_024_sort_by_date_asc(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions(m7_sample_sessions[:3], m7_sample_suitors[:3])
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=3,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(
        get_dashboard_sessions,
        dashboard_request,
        "ok",
        db,
        sort_by="date",
        sort_order="asc",
    )
    assert len(out.sessions) == 3


@pytest.mark.asyncio
async def test_m7_sessions_025_sort_by_score_desc(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    m7_sample_scores,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = _rows_for_sessions(
        [m7_sample_sessions[0], m7_sample_sessions[1], m7_sample_sessions[2]],
        [m7_sample_suitors[0], m7_sample_suitors[1], m7_sample_suitors[2]],
        [m7_sample_scores[0], m7_sample_scores[1], m7_sample_scores[2]],
    )
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=3,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(
        get_dashboard_sessions,
        dashboard_request,
        "ok",
        db,
        sort_by="score",
        sort_order="desc",
    )
    vals = [s.scores.aggregate for s in out.sessions if s.scores]
    assert sorted(vals, reverse=True) == sorted(vals, reverse=True)


@pytest.mark.asyncio
async def test_m7_sessions_026_sort_by_name(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
    m7_sample_suitors,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    m7_sample_suitors[0].name = "Charlie"
    m7_sample_suitors[1].name = "Alex"
    m7_sample_suitors[2].name = "Bella"
    rows = _rows_for_sessions(m7_sample_sessions[:3], m7_sample_suitors[:3])
    db = _build_db_for_sessions(
        make_fake_db_m7,
        fake_result_builder_m7,
        total=3,
        rows=rows,
        heart=m7_seeded_heart,
    )
    out = await _call_sessions(
        get_dashboard_sessions,
        dashboard_request,
        "ok",
        db,
        sort_by="name",
        sort_order="asc",
    )
    assert {s.suitor_name for s in out.sessions} == {"Alex", "Bella", "Charlie"}
