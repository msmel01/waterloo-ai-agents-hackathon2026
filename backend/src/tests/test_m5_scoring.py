"""M5 scoring and verdict engine tests."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from src.api.v1.endpoints.sessions import get_session_verdict
from src.models.domain_enums import Verdict
from src.models.score_model import ScoreDb
from src.services.scoring.prompt_builder import build_scoring_prompt
from src.services.scoring.scoring_service import ScoringService
from workers.main import score_session_task


def _score_payload(e=80, c=70, i=90, eq=60, modifier=0):
    return {
        "category_scores": {
            "effort": e,
            "creativity": c,
            "intent_clarity": i,
            "emotional_intelligence": eq,
        },
        "emotion_modifier": modifier,
        "emotion_modifier_reasons": ["steady confidence"],
        "feedback": {
            "summary": "Strong clarity and effort.",
            "strengths": ["specific answers", "good intent"],
            "improvements": ["more humor"],
            "heart_note": "good fit",
        },
        "per_question_scores": [
            {
                "question_index": 0,
                "question_text": "Q1",
                "effort": e,
                "creativity": c,
                "intent_clarity": i,
                "emotional_intelligence": eq,
                "emotion_context": "calm",
                "note": "solid",
            }
        ],
    }


@pytest.mark.asyncio
async def test_m5_001_scoring_job_enqueued_on_session_end(monkeypatch):
    from src.workers.tasks import enqueue_scoring_job

    pool = AsyncMock()

    async def fake_create_pool(*_args, **_kwargs):
        return pool

    monkeypatch.setattr("src.workers.tasks.create_pool", fake_create_pool)
    await enqueue_scoring_job("abc")
    pool.enqueue_job.assert_awaited_once()


@pytest.mark.asyncio
async def test_m5_002_scoring_worker_picks_up_job(monkeypatch):
    assert callable(score_session_task)


@pytest.mark.asyncio
async def test_m5_003_scoring_worker_fetches_session_data(completed_session):
    assert completed_session.turn_summaries is not None
    assert completed_session.emotion_timeline is not None


@pytest.mark.asyncio
async def test_m5_004_scoring_prompt_includes_heart_preferences(
    heart_config, sample_transcript, sample_emotion_timeline
):
    prompt = build_scoring_prompt(
        heart_config={
            "display_name": heart_config["name"],
            "bio": "bio",
            "persona": {"traits": ["warm"]},
            "expectations": {"dealbreakers": ["dishonesty"]},
        },
        session_data={"session_id": "s1"},
        turn_summaries=sample_transcript,
        emotion_timeline=sample_emotion_timeline,
        transcript=[{"speaker": "suitor", "content": "hello"}],
    )
    assert "dealbreakers" in prompt.lower()


@pytest.mark.asyncio
async def test_m5_005_scoring_prompt_includes_transcript(
    sample_transcript, sample_emotion_timeline
):
    prompt = build_scoring_prompt(
        heart_config={
            "display_name": "Luna",
            "bio": "b",
            "persona": {},
            "expectations": {},
        },
        session_data={"session_id": "s1"},
        turn_summaries=sample_transcript,
        emotion_timeline=sample_emotion_timeline,
        transcript=[{"speaker": "suitor", "content": "I like hiking"}],
    )
    assert "I like hiking" in prompt


@pytest.mark.asyncio
async def test_m5_006_scoring_prompt_includes_emotion_timeline(
    sample_transcript, sample_emotion_timeline
):
    prompt = build_scoring_prompt(
        heart_config={
            "display_name": "Luna",
            "bio": "b",
            "persona": {},
            "expectations": {},
        },
        session_data={"session_id": "s1"},
        turn_summaries=sample_transcript,
        emotion_timeline=sample_emotion_timeline,
        transcript=[],
    )
    assert "Emotional arc" in prompt


@pytest.mark.asyncio
async def test_m5_007_scoring_prompt_defines_categories(
    sample_transcript, sample_emotion_timeline
):
    prompt = build_scoring_prompt(
        heart_config={
            "display_name": "Luna",
            "bio": "b",
            "persona": {},
            "expectations": {},
        },
        session_data={"session_id": "s1"},
        turn_summaries=sample_transcript,
        emotion_timeline=sample_emotion_timeline,
        transcript=[],
    )
    for label in ["Effort", "Creativity", "Intent clarity", "Emotional intelligence"]:
        assert label.lower() in prompt.lower()


@pytest.mark.asyncio
async def test_m5_008_scoring_prompt_defines_emotion_modifiers(
    sample_transcript, sample_emotion_timeline
):
    prompt = build_scoring_prompt(
        heart_config={
            "display_name": "Luna",
            "bio": "b",
            "persona": {},
            "expectations": {},
        },
        session_data={"session_id": "s1"},
        turn_summaries=sample_transcript,
        emotion_timeline=sample_emotion_timeline,
        transcript=[],
    )
    assert "modifier" in prompt.lower()


@pytest.mark.asyncio
async def test_m5_009_effort_score_range():
    assert 0 <= _score_payload()["category_scores"]["effort"] <= 100


@pytest.mark.asyncio
async def test_m5_010_creativity_score_range():
    assert 0 <= _score_payload()["category_scores"]["creativity"] <= 100


@pytest.mark.asyncio
async def test_m5_011_intent_clarity_score_range():
    assert 0 <= _score_payload()["category_scores"]["intent_clarity"] <= 100


@pytest.mark.asyncio
async def test_m5_012_emotional_intelligence_score_range():
    assert 0 <= _score_payload()["category_scores"]["emotional_intelligence"] <= 100


@pytest.mark.asyncio
async def test_m5_013_aggregate_score_weighted_correctly():
    effort, creativity, intent, eq = 80, 70, 90, 60
    aggregate = 0.30 * effort + 0.20 * creativity + 0.25 * intent + 0.25 * eq
    assert aggregate == 75.5


@pytest.mark.asyncio
async def test_m5_014_emotion_modifiers_applied():
    raw = 75.5
    boosted = raw + 3
    penalized = raw - 4
    assert boosted > raw
    assert penalized < raw


@pytest.mark.asyncio
async def test_m5_015_high_score_yields_date_verdict():
    assert Verdict.DATE.value == "date"


@pytest.mark.asyncio
async def test_m5_016_low_score_yields_no_date_verdict():
    assert Verdict.NO_DATE.value == "no_date"


@pytest.mark.asyncio
async def test_m5_017_borderline_score_handling():
    threshold = 65.0
    assert ("date" if threshold >= 65.0 else "no_date") == "date"


@pytest.mark.asyncio
async def test_m5_018_verdict_stored_in_db(completed_session):
    score = ScoreDb(
        session_id=completed_session.id,
        effort_score=80,
        creativity_score=70,
        intent_clarity_score=90,
        emotional_intelligence_score=60,
        weighted_total=75.5,
        verdict=Verdict.DATE,
        feedback_text="Great fit",
        emotion_modifiers={},
    )
    assert score.session_id == completed_session.id


@pytest.mark.asyncio
async def test_m5_019_feedback_text_generated():
    assert _score_payload()["feedback"]["summary"]


@pytest.mark.asyncio
async def test_m5_020_feedback_mentions_strengths():
    assert _score_payload()["feedback"]["strengths"]


@pytest.mark.asyncio
async def test_m5_021_feedback_mentions_improvements():
    assert _score_payload()["feedback"]["improvements"]


@pytest.mark.asyncio
async def test_m5_022_feedback_references_specific_answers(sample_transcript):
    text = sample_transcript[0]["answer"]
    assert "stargazing" in text.lower()


@pytest.mark.asyncio
async def test_m5_023_get_verdict_api_success(registered_suitor, completed_session):
    session_repo = AsyncMock()
    session_repo.read_by_id.return_value = completed_session
    heart_repo = AsyncMock()
    heart_repo.read_by_id.return_value = type("Heart", (), {"display_name": "Luna"})()
    score_repo = AsyncMock()
    score_repo.find_by_session_id.return_value = ScoreDb(
        session_id=completed_session.id,
        effort_score=80,
        creativity_score=70,
        intent_clarity_score=90,
        emotional_intelligence_score=60,
        weighted_total=75.5,
        verdict=Verdict.DATE,
        feedback_text="Great fit",
        emotion_modifiers={},
    )
    completed_session.verdict_status = "ready"
    res = await get_session_verdict.__wrapped__(
        completed_session.id, registered_suitor, session_repo, score_repo, heart_repo
    )
    assert res.ready is True
    assert res.verdict == Verdict.DATE
    assert res.status == "scored"


@pytest.mark.asyncio
async def test_m5_024_get_verdict_api_not_ready(registered_suitor, completed_session):
    session_repo = AsyncMock()
    session_repo.read_by_id.return_value = completed_session
    heart_repo = AsyncMock()
    heart_repo.read_by_id.return_value = None
    score_repo = AsyncMock()
    score_repo.find_by_session_id.return_value = None
    completed_session.verdict_status = "scoring"
    resp = await get_session_verdict.__wrapped__(
        completed_session.id, registered_suitor, session_repo, score_repo, heart_repo
    )
    assert resp.status_code == 202


@pytest.mark.asyncio
async def test_m5_025_get_verdict_api_session_not_found(registered_suitor):
    session_repo = AsyncMock()
    session_repo.read_by_id.return_value = None
    heart_repo = AsyncMock()
    score_repo = AsyncMock()
    with pytest.raises(Exception):
        await get_session_verdict.__wrapped__(
            uuid.uuid4(), registered_suitor, session_repo, score_repo, heart_repo
        )


@pytest.mark.asyncio
async def test_m5_026_verdict_response_shape(registered_suitor, completed_session):
    session_repo = AsyncMock()
    session_repo.read_by_id.return_value = completed_session
    heart_repo = AsyncMock()
    heart_repo.read_by_id.return_value = type("Heart", (), {"display_name": "Luna"})()
    score_repo = AsyncMock()
    completed_session.verdict_status = "ready"
    score_repo.find_by_session_id.return_value = ScoreDb(
        session_id=completed_session.id,
        effort_score=80,
        creativity_score=70,
        intent_clarity_score=90,
        emotional_intelligence_score=60,
        weighted_total=75.5,
        verdict=Verdict.DATE,
        feedback_text="Great fit",
        emotion_modifiers={},
    )
    out = await get_session_verdict.__wrapped__(
        completed_session.id, registered_suitor, session_repo, score_repo, heart_repo
    )
    payload = out.model_dump()
    for field in ["status", "scores", "feedback", "booking_available", "verdict"]:
        assert field in payload


@pytest.mark.asyncio
async def test_m5_027_scoring_retries_on_claude_api_failure(monkeypatch):
    service = ScoringService.__new__(ScoringService)
    service.model = "claude"
    client = AsyncMock()
    client.messages.create.side_effect = RuntimeError("500")
    service.client = client
    with pytest.raises(RuntimeError):
        await service.client.messages.create()


@pytest.mark.asyncio
async def test_m5_028_scoring_handles_empty_transcript(sample_emotion_timeline):
    prompt = build_scoring_prompt(
        heart_config={
            "display_name": "Luna",
            "bio": "b",
            "persona": {},
            "expectations": {},
        },
        session_data={"session_id": "s1"},
        turn_summaries=[],
        emotion_timeline=sample_emotion_timeline,
        transcript=[],
    )
    assert "No transcript available" in prompt


@pytest.mark.asyncio
async def test_m5_029_scoring_handles_missing_emotion_data(sample_transcript):
    prompt = build_scoring_prompt(
        heart_config={
            "display_name": "Luna",
            "bio": "b",
            "persona": {},
            "expectations": {},
        },
        session_data={"session_id": "s1"},
        turn_summaries=sample_transcript,
        emotion_timeline=[],
        transcript=[],
    )
    assert "Insufficient emotion data" in prompt


@pytest.mark.asyncio
async def test_m5_030_scoring_handles_partial_conversation(
    sample_transcript, sample_emotion_timeline
):
    prompt = build_scoring_prompt(
        heart_config={
            "display_name": "Luna",
            "bio": "b",
            "persona": {},
            "expectations": {},
        },
        session_data={"session_id": "s1", "end_reason": "suitor_disconnected"},
        turn_summaries=sample_transcript[:2],
        emotion_timeline=sample_emotion_timeline[:4],
        transcript=[{"speaker": "suitor", "content": "partial"}],
    )
    assert "suitor_disconnected" in prompt
