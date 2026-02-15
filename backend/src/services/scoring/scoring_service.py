"""Claude-backed scoring service for completed interview sessions."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from anthropic import AsyncAnthropic

from src.core.config import config
from src.models.domain_enums import Verdict
from src.services.scoring.prompt_builder import build_scoring_prompt

logger = logging.getLogger(__name__)

SCORING_WEIGHTS: dict[str, float] = {
    "effort": 0.30,
    "creativity": 0.20,
    "intent_clarity": 0.25,
    "emotional_intelligence": 0.25,
}


class ScoringService:
    """Scores completed interviews with Claude and normalizes output."""

    def __init__(self) -> None:
        if config.ANTHROPIC_API_KEY is None:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured")

        self.client = AsyncAnthropic(
            api_key=config.ANTHROPIC_API_KEY.get_secret_value()
        )
        self.model = "claude-sonnet-4-20250514"

    async def score_session(
        self,
        *,
        heart_config: dict[str, Any],
        session_data: dict[str, Any],
        turn_summaries: list[dict[str, Any]],
        emotion_timeline: list[dict[str, Any]],
        transcript: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Return normalized score payload ready for the scores table."""
        prompt = build_scoring_prompt(
            heart_config=heart_config,
            session_data=session_data,
            turn_summaries=turn_summaries,
            emotion_timeline=emotion_timeline,
            transcript=transcript,
        )

        started = time.monotonic()
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}],
        )
        scoring_duration_ms = int((time.monotonic() - started) * 1000)

        response_text = self._extract_text(response)
        result = self._parse_json(response_text)

        category_scores = result.get("scores") or result.get("category_scores", {})
        effort = self._clamp(category_scores.get("effort", 50), 0, 100)
        creativity = self._clamp(category_scores.get("creativity", 50), 0, 100)
        intent_clarity = self._clamp(category_scores.get("intent_clarity", 50), 0, 100)
        emotional_intelligence = self._clamp(
            category_scores.get("emotional_intelligence", 50), 0, 100
        )

        emotion_modifiers_payload = result.get("emotion_modifiers")
        if isinstance(emotion_modifiers_payload, dict):
            emotion_modifier = self._clamp(
                sum(
                    float(emotion_modifiers_payload.get(key, 0) or 0)
                    for key in [
                        "confidence_boost",
                        "anxiety_context",
                        "enthusiasm_bonus",
                        "discomfort_sensitivity",
                    ]
                ),
                -10,
                10,
            )
            emotion_modifiers = {
                "confidence_boost": float(
                    emotion_modifiers_payload.get("confidence_boost", 0) or 0
                ),
                "anxiety_context": float(
                    emotion_modifiers_payload.get("anxiety_context", 0) or 0
                ),
                "enthusiasm_bonus": float(
                    emotion_modifiers_payload.get("enthusiasm_bonus", 0) or 0
                ),
                "discomfort_sensitivity": float(
                    emotion_modifiers_payload.get("discomfort_sensitivity", 0) or 0
                ),
                "total": 0.0,
            }
            emotion_modifiers["total"] = round(emotion_modifier, 2)
        else:
            emotion_modifier = self._clamp(result.get("emotion_modifier", 0), -10, 10)
            emotion_modifiers = {"voice_modifier": round(float(emotion_modifier), 2)}

        raw_score = (
            effort * SCORING_WEIGHTS["effort"]
            + creativity * SCORING_WEIGHTS["creativity"]
            + intent_clarity * SCORING_WEIGHTS["intent_clarity"]
            + emotional_intelligence * SCORING_WEIGHTS["emotional_intelligence"]
        )

        final_score = self._clamp(raw_score + emotion_modifier, 0, 100)
        verdict_threshold = float(config.VERDICT_THRESHOLD)
        verdict = Verdict.DATE if final_score >= verdict_threshold else Verdict.NO_DATE

        feedback = result.get("feedback", {})
        feedback_summary = str(feedback.get("summary") or "")
        if not feedback_summary:
            feedback_summary = "Interview scored successfully."
        feedback_json = {
            "summary": feedback_summary,
            "strengths": self._as_list(feedback.get("strengths")),
            "improvements": self._as_list(feedback.get("improvements")),
            "favorite_moment": str(feedback.get("favorite_moment") or ""),
        }

        return {
            "effort_score": float(effort),
            "creativity_score": float(creativity),
            "intent_clarity_score": float(intent_clarity),
            "emotional_intelligence_score": float(emotional_intelligence),
            "weighted_total": round(raw_score, 2),
            "raw_score": round(raw_score, 2),
            "final_score": round(final_score, 2),
            "emotion_modifier": float(emotion_modifier),
            "emotion_modifiers": emotion_modifiers,
            "emotion_modifier_reasons": self._as_list(
                result.get("emotion_modifier_reasons")
            ),
            "verdict": verdict,
            "verdict_threshold": verdict_threshold,
            "feedback_text": feedback_summary,
            "feedback_summary": feedback_summary,
            "feedback_strengths": feedback_json["strengths"],
            "feedback_improvements": feedback_json["improvements"],
            "feedback_json": feedback_json,
            "feedback_heart_note": (
                str(feedback.get("heart_note"))
                if feedback.get("heart_note") is not None
                else None
            ),
            "per_question_scores": result.get("per_question_scores", []),
            "claude_model": self.model,
            "claude_input_tokens": getattr(response.usage, "input_tokens", None),
            "claude_output_tokens": getattr(response.usage, "output_tokens", None),
            "scoring_duration_ms": scoring_duration_ms,
            "raw_llm_response": response_text,
        }

    def _extract_text(self, response: Any) -> str:
        chunks = getattr(response, "content", []) or []
        texts: list[str] = []
        for chunk in chunks:
            txt = getattr(chunk, "text", None)
            if txt:
                texts.append(txt)
        return "\n".join(texts).strip()

    def _parse_json(self, response_text: str) -> dict[str, Any]:
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines:
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:  # pragma: no cover - external API output
            logger.exception(
                "Claude returned invalid JSON (length=%s, preview=%r)",
                len(text),
                text[:120],
            )
            raise ValueError("Claude scoring output was not valid JSON") from exc

        if not isinstance(data, dict):
            raise ValueError("Claude scoring output must be an object")
        return data

    @staticmethod
    def _as_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if item is not None]

    @staticmethod
    def _clamp(value: Any, min_value: float, max_value: float) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = min_value
        return max(min_value, min(max_value, numeric))
