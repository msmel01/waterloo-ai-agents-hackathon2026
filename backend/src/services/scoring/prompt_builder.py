"""Prompt construction helpers for Claude-based interview scoring."""

from __future__ import annotations

from typing import Any


def format_list(items: list[Any]) -> str:
    if not items:
        return "None specified"
    return "\n".join(f"- {item}" for item in items)


def format_expectations(expectations: dict[str, Any] | None) -> str:
    if not expectations:
        return "No specific expectations defined."

    parts: list[str] = []
    if expectations.get("looking_for"):
        parts.append(f"Looking for: {expectations['looking_for']}")
    if expectations.get("values") and isinstance(expectations["values"], list):
        parts.append(f"Values: {', '.join(expectations['values'])}")
    if expectations.get("must_haves") and isinstance(expectations["must_haves"], list):
        parts.append(f"Must-haves: {', '.join(expectations['must_haves'])}")
    if expectations.get("communication_preferences"):
        parts.append(
            f"Communication preferences: {expectations['communication_preferences']}"
        )

    return "\n".join(parts) if parts else "No specific expectations defined."


def format_transcript(transcript: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for turn in transcript:
        speaker = str(turn.get("speaker", "")).lower()
        label = "Avatar" if speaker == "avatar" else "Suitor"
        content = str(turn.get("content", "")).strip()
        if content:
            lines.append(f"{label}: {content}")
    return "\n\n".join(lines) if lines else "No transcript available."


def format_turn_analysis(turn_summaries: list[dict[str, Any]]) -> str:
    if not turn_summaries:
        return "No per-turn analysis available."

    sections: list[str] = []
    for turn in turn_summaries:
        raw_q_idx = turn.get("question_index", 0)
        try:
            safe_q_idx = int(raw_q_idx)
        except (TypeError, ValueError):
            safe_q_idx = 0
        q_idx = safe_q_idx + 1
        q_text = str(turn.get("question_text", "")).strip() or "Unknown question"
        quality = str(turn.get("response_quality", "unknown"))
        summary = str(turn.get("response_summary", "")).strip() or "No summary"
        block = [
            f"Q{q_idx}: {q_text}",
            f"Agent assessment: {quality}",
            f"Summary: {summary}",
        ]
        sections.append("\n".join(block))

    return "\n\n".join(sections)


def build_scoring_prompt(
    heart_config: dict[str, Any],
    session_data: dict[str, Any],
    turn_summaries: list[dict[str, Any]],
    transcript: list[dict[str, Any]],
) -> str:
    display_name = heart_config.get("display_name") or heart_config.get(
        "profile", {}
    ).get("display_name", "the Heart")
    bio = heart_config.get("bio") or heart_config.get("profile", {}).get("bio", "")
    persona = heart_config.get("persona", {})
    expectations = heart_config.get("expectations", {})

    transcript_text = format_transcript(transcript)
    turn_analysis = format_turn_analysis(turn_summaries)

    return f"""You are the scoring engine for Valentine Hotline, an AI-powered dating screening system.

## The Heart
Name: {display_name}
Bio: {bio}
Persona: {persona}

What {display_name} is looking for:
{format_expectations(expectations)}

Dealbreakers:
{format_list(expectations.get("dealbreakers", []))}

## Session metadata
{session_data}

## Full Transcript
{transcript_text}

## Per-question analysis
{turn_analysis}

## Scoring rubric (0-100)
1. Effort (30%)
2. Creativity (20%)
3. Intent clarity (25%)
4. Emotional intelligence (25%)

Return ONLY valid JSON with this exact structure:
{{
  "scores": {{
    "effort": 0,
    "creativity": 0,
    "intent_clarity": 0,
    "emotional_intelligence": 0
  }},
  "feedback": {{
    "summary": "...",
    "strengths": ["..."],
    "improvements": ["..."],
    "favorite_moment": "...",
    "heart_note": "..."
  }},
  "per_question_scores": [
    {{
      "question_index": 0,
      "question_text": "...",
      "effort": 0,
      "creativity": 0,
      "intent_clarity": 0,
      "emotional_intelligence": 0,
      "note": "..."
    }}
  ]
}}
"""
