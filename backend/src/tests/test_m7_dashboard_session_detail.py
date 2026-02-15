from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from src.api.v1.endpoints.dashboard import get_dashboard_session_detail
from src.models.domain_enums import SessionStatus, Verdict


def _build_detail_db(make_fake_db_m7, fake_result_builder_m7, row, *, heart):
    return make_fake_db_m7([fake_result_builder_m7(first_value=row)], heart=heart)


@pytest.mark.asyncio
async def test_m7_detail_001_returns_full_session_data(
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
    row = (
        m7_sample_sessions[0],
        m7_sample_suitors[0],
        m7_sample_scores[0],
        m7_sample_booking,
    )
    db = _build_detail_db(
        make_fake_db_m7, fake_result_builder_m7, row, heart=m7_seeded_heart
    )

    out = await get_dashboard_session_detail(
        m7_sample_sessions[0].id, dashboard_request, "ok", db
    )
    payload = out.model_dump()
    for key in [
        "session_id",
        "suitor",
        "session",
        "transcript",
        "scores",
        "verdict",
        "feedback",
        "booking",
    ]:
        assert key in payload


@pytest.mark.asyncio
async def test_m7_detail_002_suitor_data_correct(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    row = (m7_sample_sessions[0], m7_sample_suitors[0], None, None)
    db = _build_detail_db(
        make_fake_db_m7, fake_result_builder_m7, row, heart=m7_seeded_heart
    )
    out = await get_dashboard_session_detail(
        m7_sample_sessions[0].id, dashboard_request, "ok", db
    )
    assert out.suitor.name == m7_sample_suitors[0].name
    assert out.suitor.intro_message == m7_sample_suitors[0].intro_message
    assert out.suitor.created_at == m7_sample_suitors[0].created_at


@pytest.mark.asyncio
async def test_m7_detail_003_session_metadata_correct(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    row = (m7_sample_sessions[0], m7_sample_suitors[0], None, None)
    db = _build_detail_db(
        make_fake_db_m7, fake_result_builder_m7, row, heart=m7_seeded_heart
    )
    out = await get_dashboard_session_detail(
        m7_sample_sessions[0].id, dashboard_request, "ok", db
    )
    assert out.session.status == SessionStatus.COMPLETED.value
    assert out.session.started_at == m7_sample_sessions[0].started_at
    assert out.session.ended_at == m7_sample_sessions[0].ended_at
    assert out.session.duration_seconds is not None
    assert out.session.livekit_room_name == m7_sample_sessions[0].livekit_room_name


@pytest.mark.asyncio
async def test_m7_detail_004_transcript_returned_in_order(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    row = (m7_sample_sessions[0], m7_sample_suitors[0], None, None)
    db = _build_detail_db(
        make_fake_db_m7, fake_result_builder_m7, row, heart=m7_seeded_heart
    )
    out = await get_dashboard_session_detail(
        m7_sample_sessions[0].id, dashboard_request, "ok", db
    )
    assert len(out.transcript) == 5
    assert [t.turn for t in out.transcript] == [1, 2, 3, 4, 5]


@pytest.mark.asyncio
async def test_m7_detail_005_scores_with_weights_and_labels(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    m7_sample_scores,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    row = (m7_sample_sessions[0], m7_sample_suitors[0], m7_sample_scores[0], None)
    db = _build_detail_db(
        make_fake_db_m7, fake_result_builder_m7, row, heart=m7_seeded_heart
    )
    out = await get_dashboard_session_detail(
        m7_sample_sessions[0].id, dashboard_request, "ok", db
    )
    assert out.scores is not None
    assert out.scores.effort.weight == 0.30
    assert out.scores.effort.label == "Effort & Thoughtfulness"
    assert out.scores.creativity.weight == 0.20
    assert out.scores.intent_clarity.weight == 0.25
    assert out.scores.emotional_intelligence.weight == 0.25
    assert out.scores.aggregate >= 0


@pytest.mark.asyncio
async def test_m7_detail_006_feedback_structured(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    m7_sample_scores,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    row = (m7_sample_sessions[0], m7_sample_suitors[0], m7_sample_scores[0], None)
    db = _build_detail_db(
        make_fake_db_m7, fake_result_builder_m7, row, heart=m7_seeded_heart
    )
    out = await get_dashboard_session_detail(
        m7_sample_sessions[0].id, dashboard_request, "ok", db
    )
    assert isinstance(out.feedback.summary, str)
    assert isinstance(out.feedback.strengths, list)
    assert isinstance(out.feedback.improvements, list)
    assert isinstance(out.feedback.favorite_moment, str)


@pytest.mark.asyncio
async def test_m7_detail_007_booking_data_when_booked(
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
    row = (
        m7_sample_sessions[0],
        m7_sample_suitors[0],
        m7_sample_scores[0],
        m7_sample_booking,
    )
    db = _build_detail_db(
        make_fake_db_m7, fake_result_builder_m7, row, heart=m7_seeded_heart
    )
    out = await get_dashboard_session_detail(
        m7_sample_sessions[0].id, dashboard_request, "ok", db
    )
    assert out.booking is not None
    assert out.booking.cal_event_id == m7_sample_booking.calcom_booking_id
    assert out.booking.slot_start == m7_sample_booking.scheduled_at
    assert out.booking.suitor_email == m7_sample_booking.suitor_email
    assert out.booking.suitor_notes == m7_sample_booking.suitor_notes


@pytest.mark.asyncio
async def test_m7_detail_008_no_scores_yet(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    row = (m7_sample_sessions[0], m7_sample_suitors[0], None, None)
    db = _build_detail_db(
        make_fake_db_m7, fake_result_builder_m7, row, heart=m7_seeded_heart
    )
    out = await get_dashboard_session_detail(
        m7_sample_sessions[0].id, dashboard_request, "ok", db
    )
    assert out.scores is None
    assert out.verdict is None
    assert out.feedback is None


@pytest.mark.asyncio
async def test_m7_detail_009_no_booking_for_date_verdict(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    m7_sample_scores,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    row = (m7_sample_sessions[0], m7_sample_suitors[0], m7_sample_scores[0], None)
    db = _build_detail_db(
        make_fake_db_m7, fake_result_builder_m7, row, heart=m7_seeded_heart
    )
    out = await get_dashboard_session_detail(
        m7_sample_sessions[0].id, dashboard_request, "ok", db
    )
    assert out.verdict == Verdict.DATE.value
    assert out.booking is None


@pytest.mark.asyncio
async def test_m7_detail_010_no_booking_for_no_date_verdict(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    m7_sample_scores,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    row = (m7_sample_sessions[1], m7_sample_suitors[1], m7_sample_scores[1], None)
    db = _build_detail_db(
        make_fake_db_m7, fake_result_builder_m7, row, heart=m7_seeded_heart
    )
    out = await get_dashboard_session_detail(
        m7_sample_sessions[1].id, dashboard_request, "ok", db
    )
    assert out.verdict == Verdict.NO_DATE.value
    assert out.booking is None


@pytest.mark.asyncio
async def test_m7_detail_011_failed_session(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    row = (m7_sample_sessions[4], m7_sample_suitors[4], None, None)
    db = _build_detail_db(
        make_fake_db_m7, fake_result_builder_m7, row, heart=m7_seeded_heart
    )
    out = await get_dashboard_session_detail(
        m7_sample_sessions[4].id, dashboard_request, "ok", db
    )
    assert out.session.status == SessionStatus.FAILED.value
    assert len(out.transcript) == 2
    assert out.scores is None


@pytest.mark.asyncio
async def test_m7_detail_012_empty_transcript(
    dashboard_request,
    m7_seeded_heart,
    m7_sample_suitors,
    m7_sample_sessions,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    m7_sample_sessions[0].turn_summaries = {"turns": []}
    row = (m7_sample_sessions[0], m7_sample_suitors[0], None, None)
    db = _build_detail_db(
        make_fake_db_m7, fake_result_builder_m7, row, heart=m7_seeded_heart
    )
    out = await get_dashboard_session_detail(
        m7_sample_sessions[0].id, dashboard_request, "ok", db
    )
    assert out.transcript == []


@pytest.mark.asyncio
async def test_m7_detail_013_session_not_found(
    dashboard_request,
    m7_seeded_heart,
    make_fake_db_m7,
    fake_result_builder_m7,
):
    dashboard_request.app.state.heart_id = m7_seeded_heart.id
    db = _build_detail_db(
        make_fake_db_m7, fake_result_builder_m7, None, heart=m7_seeded_heart
    )
    with pytest.raises(HTTPException) as exc:
        await get_dashboard_session_detail(uuid.uuid4(), dashboard_request, "ok", db)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_m7_detail_014_invalid_session_id_format(
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
        "/api/v1/dashboard/sessions/not-a-uuid", headers=dashboard_headers
    )
    assert resp.status_code in (404, 422)
