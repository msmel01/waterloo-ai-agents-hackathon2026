"""Unit tests for public endpoint helper functions."""

from src.api.v1.endpoints.public import _build_persona_preview, _estimate_duration


def test_estimate_duration_for_zero_questions_has_minimum_floor() -> None:
    assert _estimate_duration(0) == "1-2 minutes"


def test_estimate_duration_scales_with_question_count() -> None:
    assert _estimate_duration(5) == "5-10 minutes"


def test_build_persona_preview_handles_missing_persona() -> None:
    assert _build_persona_preview(None) is None


def test_build_persona_preview_formats_multiple_traits() -> None:
    persona = {"traits": ["witty", "direct", "warm", "playful"]}
    assert _build_persona_preview(persona) == "witty, direct, and warm"
