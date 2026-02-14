"""Hume emotion tracking helpers for interview sessions."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class HumeEmotionTracker:
    """Track rolling emotion signals from suitor audio for one session."""

    def __init__(self, api_key: str, session_id: str):
        self.api_key = api_key
        self.session_id = session_id
        self.emotions_history: list[dict] = []
        self.latest_emotions: dict | None = None
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self, room: Any) -> None:
        """Start async tracking loop bound to one LiveKit room."""
        self._running = True
        self._task = asyncio.create_task(self._track_loop(room))

    async def _track_loop(self, room: Any) -> None:
        """Track emotion stream events. Stub for M3 MVP until WS integration finalizes."""
        _ = room
        while self._running:
            # Real-time Hume streaming integration belongs here.
            await asyncio.sleep(1)

    def get_latest_emotions(self) -> dict | None:
        """Return latest normalized emotion snapshot."""
        return self.latest_emotions

    def get_emotion_timeline(self) -> list[dict]:
        """Return full timeline collected so far."""
        return self.emotions_history

    async def stop(self) -> None:
        """Stop tracking loop and cancel background task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def _aggregate_emotions(self, hume_predictions: list[dict]) -> dict:
        """Map raw Hume emotions into project-specific signals."""
        if not hume_predictions:
            return {}

        scores = {entry["name"]: entry["score"] for entry in hume_predictions}

        return {
            "confidence": max(
                scores.get("Confidence", 0),
                scores.get("Determination", 0),
                scores.get("Pride", 0),
            ),
            "hesitation": max(
                scores.get("Anxiety", 0),
                scores.get("Doubt", 0),
                scores.get("Confusion", 0),
                scores.get("Embarrassment", 0),
            ),
            "enthusiasm": max(
                scores.get("Joy", 0),
                scores.get("Excitement", 0),
                scores.get("Interest", 0),
                scores.get("Amusement", 0),
            ),
            "warmth": max(
                scores.get("Admiration", 0),
                scores.get("Love", 0),
                scores.get("Gratitude", 0),
            ),
            "discomfort": max(
                scores.get("Distress", 0),
                scores.get("Fear", 0),
                scores.get("Awkwardness", 0),
            ),
            "raw_top_emotions": sorted(
                hume_predictions, key=lambda item: item["score"], reverse=True
            )[:5],
        }
