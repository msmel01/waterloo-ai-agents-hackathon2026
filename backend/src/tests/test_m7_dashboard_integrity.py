from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from src.api.v1.endpoints.dashboard import (
    get_dashboard_session_detail,
    get_dashboard_sessions,
    get_dashboard_stats,
)


def _build_stats_db(make_fake_db_m7, fake_result_builder_m7, *, heart, total_sessions):
    return make_fake_db_m7(
        [
            fake_result_builder_m7(scalar_value=5),
            fake_result_builder_m7(all_values=[("completed", total_sessions)]),
            fake_result_builder_m7(all_values=[("date", 2), ("no_date", 1)]),
            fake_result_builder_m7(one_value=(80.0, 70.0, 75.0, 72.0, 74.3)),
            fake_result_builder_m7(all_values=[("good", 3)]),
            fake_result_builder_m7(scalar_value=1),
            fake_result_builder_m7(scalar_value=2),
            fake_result_builder_m7(scalar_value=3),
            fake_result_builder_m7(scalar_value=1),
            fake_result_builder_m7(scalar_value=1),
        ],
        heart=heart,
    )


def _build_sessions_db(make_fake_db_m7, fake_result_builder_m7, *, heart, rows, total):
    return make_fake_db_m7(
        [
            fake_result_builder_m7(scalar_value=total),
            fake_result_builder_m7(all_values=rows),
        ],
        heart=heart,
    )


async def _call_sessions(func, request, auth, db, **kwargs):
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
async def test_m7_integrity_001_stats_consistent_with_session_list(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_sessions,
    m7_sample_suitors,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    stats_db = _build_stats_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        heart=m7_seeded_heart,
        total_sessions=10,
    )
    stats = await get_dashboard_stats(dashboard_request, "ok", stats_db)

    rows = [(m7_sample_sessions[0], m7_sample_suitors[0], None, None, None)]
    sessions_db = _build_sessions_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        heart=m7_seeded_heart,
        rows=rows,
        total=10,
    )
    session_list = await _call_sessions(
        get_dashboard_sessions, dashboard_request, "ok", sessions_db
    )
    assert stats.total_sessions == session_list.pagination.total


@pytest.mark.asyncio
async def test_m7_integrity_002_session_detail_matches_list_summary(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_sessions,
    m7_sample_suitors,
    m7_sample_scores,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    list_rows = [
        (
            m7_sample_sessions[0],
            m7_sample_suitors[0],
            m7_sample_scores[0],
            None,
            m7_sample_scores[0].final_score,
        )
    ]
    list_db = _build_sessions_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        heart=m7_seeded_heart,
        rows=list_rows,
        total=1,
    )
    listing = await _call_sessions(
        get_dashboard_sessions, dashboard_request, "ok", list_db
    )

    detail_db = make_fake_db_m7(
        [
            fake_result_builder_m7(
                first_value=(
                    m7_sample_sessions[0],
                    m7_sample_suitors[0],
                    m7_sample_scores[0],
                    None,
                )
            )
        ],
        heart=m7_seeded_heart,
    )
    detail = await get_dashboard_session_detail(
        m7_sample_sessions[0].id, dashboard_request, "ok", detail_db
    )

    assert listing.sessions[0].session_id == detail.session_id
    assert listing.sessions[0].suitor_name == detail.suitor.name
    assert listing.sessions[0].verdict == detail.verdict


@pytest.mark.asyncio
async def test_m7_integrity_003_concurrent_stat_requests(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id

    async def _run_one():
        db = _build_stats_db(
            make_fake_db_m7,
            fake_result_builder_m7,
            heart=m7_seeded_heart,
            total_sessions=4,
        )
        out = await get_dashboard_stats(dashboard_request, "ok", db)
        return out.total_sessions, out.total_dates

    results = await asyncio.gather(*[_run_one() for _ in range(10)])
    assert all(pair == results[0] for pair in results)


@pytest.mark.asyncio
async def test_m7_integrity_004_session_list_no_cross_heart_leakage(
    m7_seeded_heart,
    m7_sample_sessions,
):
    assert all(sess.heart_id == m7_seeded_heart.id for sess in m7_sample_sessions)


@pytest.mark.asyncio
async def test_m7_integrity_005_large_dataset_pagination(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_sessions,
    m7_sample_suitors,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = [
        (m7_sample_sessions[i % 5], m7_sample_suitors[i % 5], None, None, None)
        for i in range(20)
    ]
    db = _build_sessions_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        heart=m7_seeded_heart,
        rows=rows,
        total=500,
    )
    out = await _call_sessions(
        get_dashboard_sessions, dashboard_request, "ok", db, page=25, per_page=20
    )
    assert len(out.sessions) == 20
    assert out.pagination.total == 500
    assert out.pagination.total_pages == 25


@pytest.mark.asyncio
async def test_m7_integrity_006_special_characters_in_suitor_name(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_sessions,
    m7_sample_suitors,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    m7_sample_suitors[0].name = "O'Brien-Smith 🎉"
    rows = [(m7_sample_sessions[0], m7_sample_suitors[0], None, None, None)]
    db = _build_sessions_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        heart=m7_seeded_heart,
        rows=rows,
        total=1,
    )
    out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    assert out.sessions[0].suitor_name == "O'Brien-Smith 🎉"


@pytest.mark.asyncio
async def test_m7_integrity_007_search_sql_injection_safe(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_sessions_db(
        make_fake_db_m7, fake_result_builder_m7, heart=m7_seeded_heart, rows=[], total=0
    )
    out = await _call_sessions(
        get_dashboard_sessions,
        dashboard_request,
        "ok",
        db,
        search="'; DROP TABLE sessions; --",
    )
    assert out.sessions == []


@pytest.mark.asyncio
async def test_m7_integrity_008_very_long_transcript(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    start = datetime.now(timezone.utc)
    m7_sample_sessions[0].turn_summaries = {
        "turns": [
            {
                "turn": i + 1,
                "question": f"Q{i + 1}",
                "answer": f"A{i + 1}",
                "timestamp": (start + timedelta(minutes=i)).isoformat(),
            }
            for i in range(20)
        ]
    }
    db = make_fake_db_m7(
        [
            fake_result_builder_m7(
                first_value=(m7_sample_sessions[0], m7_sample_suitors[0], None, None)
            )
        ],
        heart=m7_seeded_heart,
    )
    out = await get_dashboard_session_detail(
        m7_sample_sessions[0].id, dashboard_request, "ok", db
    )
    assert len(out.transcript) == 20


@pytest.mark.asyncio
async def test_m7_integrity_009_null_intro_message(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    rows = [(m7_sample_sessions[1], m7_sample_suitors[1], None, None, None)]
    db = _build_sessions_db(
        make_fake_db_m7,
        fake_result_builder_m7,
        heart=m7_seeded_heart,
        rows=rows,
        total=1,
    )
    list_out = await _call_sessions(get_dashboard_sessions, dashboard_request, "ok", db)
    assert list_out.sessions[0].suitor_intro is None

    detail_db = make_fake_db_m7(
        [
            fake_result_builder_m7(
                first_value=(m7_sample_sessions[1], m7_sample_suitors[1], None, None)
            )
        ],
        heart=m7_seeded_heart,
    )
    detail_out = await get_dashboard_session_detail(
        m7_sample_sessions[1].id, dashboard_request, "ok", detail_db
    )
    assert detail_out.suitor.intro_message is None


@pytest.mark.asyncio
async def test_m7_integrity_010_feedback_json_null(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    m7_sample_scores,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    score = m7_sample_scores[0]
    score.feedback_json = None
    score.feedback_summary = ""
    score.feedback_text = ""
    score.feedback_strengths = []
    score.feedback_improvements = []
    db = make_fake_db_m7(
        [
            fake_result_builder_m7(
                first_value=(m7_sample_sessions[0], m7_sample_suitors[0], score, None)
            )
        ],
        heart=m7_seeded_heart,
    )
    out = await get_dashboard_session_detail(
        m7_sample_sessions[0].id, dashboard_request, "ok", db
    )
    assert out.feedback is not None
