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
        q_idx = int(turn.get("question_index", 0)) + 1
        q_text = str(turn.get("question_text", "")).strip() or "Unknown question"
        quality = str(turn.get("response_quality", "unknown"))
        summary = str(turn.get("response_summary", "")).strip() or "No summary"
        emotions = (
            turn.get("emotions") if isinstance(turn.get("emotions"), dict) else {}
        )

        emotion_lines: list[str] = []
        if emotions:
            dominant = emotions.get("dominant_emotion", "Unknown")
            dominant_score = float(emotions.get("dominant_score", 0) or 0)
            emotion_lines.append(f"Voice emotion: {dominant} ({dominant_score:.0%})")

            notable: list[str] = []
            for key, label, threshold in [
                ("confidence", "confident", 0.5),
                ("anxiety", "anxious", 0.5),
                ("enthusiasm", "enthusiastic", 0.5),
                ("warmth", "warm", 0.4),
            ]:
                val = float(emotions.get(key, 0) or 0)
                if val > threshold:
                    notable.append(f"{label} ({val:.0%})")
            if notable:
                emotion_lines.append(f"Notable signals: {', '.join(notable)}")

        block = [
            f"Q{q_idx}: {q_text}",
            f"Agent assessment: {quality}",
            f"Summary: {summary}",
        ]
        block.extend(emotion_lines)
        sections.append("\n".join(block))

    return "\n\n".join(sections)


def compute_emotion_arc(timeline: list[dict[str, Any]]) -> str:
    if not timeline or len(timeline) < 2:
        return "Insufficient emotion data for arc analysis."

    total = len(timeline)
    first_third = timeline[: max(1, total // 3)]
    middle_third = timeline[total // 3 : max(total // 3 + 1, 2 * total // 3)]  # noqa
    last_third = timeline[max(1, 2 * total // 3) :]

    def avg(points: list[dict[str, Any]], key: str) -> float:
        if not points:
            return 0.0
        return sum(float(p.get(key, 0) or 0) for p in points) / len(points)

    start_conf = avg(first_third, "confidence")
    end_conf = avg(last_third, "confidence")
    start_anx = avg(first_third, "anxiety")
    end_anx = avg(last_third, "anxiety")
    avg_enth = avg(timeline, "enthusiasm")
    avg_warmth = avg(timeline, "warmth")

    parts: list[str] = []
    if start_conf < end_conf - 0.1:
        parts.append("Confidence grew over the interview")
    elif start_conf > end_conf + 0.1:
        parts.append("Confidence declined over the interview")

    if start_anx > 0.4 and end_anx < 0.3:
        parts.append("Initial nervousness settled as the conversation progressed")
    elif end_anx > start_anx + 0.15:
        parts.append("Anxiety increased as the interview continued")

    if avg_enth > 0.5:
        parts.append(f"High overall enthusiasm ({avg_enth:.0%})")
    elif avg_enth < 0.2:
        parts.append(f"Low overall enthusiasm ({avg_enth:.0%})")

    if avg_warmth > 0.4:
        parts.append(f"Consistently warm tone ({avg_warmth:.0%})")

    if not parts:
        parts.append("Emotionally stable throughout with no major shifts")

    return "Emotional arc: " + ". ".join(parts) + "."


def build_scoring_prompt(
    heart_config: dict[str, Any],
    session_data: dict[str, Any],
    turn_summaries: list[dict[str, Any]],
    emotion_timeline: list[dict[str, Any]],
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
    emotion_summary = compute_emotion_arc(emotion_timeline)

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

## Emotional arc
{emotion_summary}

## Scoring rubric (0-100)
1. Effort (30%)
2. Creativity (20%)
3. Intent clarity (25%)
4. Emotional intelligence (25%)

Apply emotion modifier in range -10..+10 based on voice/emotion signals.

Return ONLY valid JSON:
{{
  "per_question_scores": [
    {{
      "question_index": 0,
      "question_text": "...",
      "effort": 0,
      "creativity": 0,
      "intent_clarity": 0,
      "emotional_intelligence": 0,
      "emotion_context": "...",
      "note": "..."
    }}
  ],
  "category_scores": {{
    "effort": 0,
    "creativity": 0,
    "intent_clarity": 0,
    "emotional_intelligence": 0
  }},
  "emotion_modifier": 0,
  "emotion_modifier_reasons": ["..."],
  "feedback": {{
    "summary": "...",
    "strengths": ["..."],
    "improvements": ["..."],
    "heart_note": "..."
  }}
}}
"""
