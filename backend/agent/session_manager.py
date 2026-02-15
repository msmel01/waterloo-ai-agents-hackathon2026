"""In-memory interview session state for LiveKit agent runtime."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class ConversationTurn:
    """Summarized response for one screening question."""

    question_index: int
    question_text: str
    response_summary: str
    response_quality: str
    timestamp: float


class RambleDetector:
    """Detect oversized suitor turns to help the agent interrupt politely."""

    def __init__(self, time_threshold: float = 45.0, word_threshold: int = 200):
        self.time_threshold = time_threshold
        self.word_threshold = word_threshold
        self.current_turn_start: float | None = None
        self.current_turn_words = 0

    def on_user_speech(self, text: str) -> None:
        """Track partial transcript chunks for one turn."""
        if self.current_turn_start is None:
            self.current_turn_start = time.time()
        self.current_turn_words += len(text.split())

    def should_interrupt(self) -> bool:
        """Return True if this turn exceeded duration/word thresholds."""
        if self.current_turn_start is None:
            return False
        elapsed = time.time() - self.current_turn_start
        return (
            elapsed > self.time_threshold
            or self.current_turn_words > self.word_threshold
        )

    def reset(self) -> None:
        """Reset counters when a turn commits."""
        self.current_turn_start = None
        self.current_turn_words = 0


class SessionManager:
    """Tracks question progress and transcript state for one interview."""

    def __init__(
        self, session_id: str, questions: list[dict], max_duration_seconds: int = 600
    ):
        self.session_id = session_id
        self.questions = questions
        self.max_duration = max_duration_seconds
        self.current_question_index = 0
        self.turns: list[ConversationTurn] = []
        self.started_at = time.time()
        self.ended_at: float | None = None
        self.end_reason: str | None = None
        self.full_transcript: list[dict] = []
        self.ramble_detector = RambleDetector()

    def get_next_question(self) -> dict | None:
        """Return next question or None when done."""
        if self.current_question_index >= len(self.questions):
            return None
        question = self.questions[self.current_question_index]
        return {
            "text": question["text"],
            "index": self.current_question_index,
            "required": question.get("required", True),
        }

    def record_response(
        self,
        question_index: int,
        response_summary: str,
        response_quality: str,
    ):
        """Store summarized answer and advance question index."""
        turn = ConversationTurn(
            question_index=question_index,
            question_text=self.questions[question_index]["text"],
            response_summary=response_summary,
            response_quality=response_quality,
            timestamp=time.time(),
        )
        self.turns.append(turn)
        self.current_question_index = question_index + 1
        self.ramble_detector.reset()

    def questions_remaining(self) -> int:
        """Return number of unasked screening questions."""
        return max(0, len(self.questions) - self.current_question_index)

    def add_transcript_entry(self, speaker: str, text: str):
        """Append raw transcript event."""
        self.full_transcript.append(
            {
                "speaker": speaker,
                "text": text,
                "timestamp": time.time(),
                "index": len(self.full_transcript),
            }
        )
        if speaker == "suitor":
            self.ramble_detector.on_user_speech(text)

    def is_overtime(self) -> bool:
        """True when session duration has exceeded configured max."""
        return (time.time() - self.started_at) > self.max_duration

    def end(self, reason: str) -> None:
        """Mark session ended and capture reason."""
        self.ended_at = time.time()
        self.end_reason = reason

    def get_session_data(self) -> dict:
        """Serialize all tracked state for persistence/scoring."""
        return {
            "session_id": self.session_id,
            "turns": [
                {
                    "question_index": t.question_index,
                    "question_text": t.question_text,
                    "response_summary": t.response_summary,
                    "response_quality": t.response_quality,
                    "timestamp": t.timestamp,
                }
                for t in self.turns
            ],
            "full_transcript": self.full_transcript,
            "started_at": self.started_at,
            "ended_at": self.ended_at or time.time(),
            "end_reason": self.end_reason or "unknown",
            "duration_seconds": (self.ended_at or time.time()) - self.started_at,
            "questions_asked": self.current_question_index,
            "total_questions": len(self.questions),
        }
