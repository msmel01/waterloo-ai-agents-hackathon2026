"""Hume Expression Measurement streaming tracker for live sessions."""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import wave
from collections import deque
from typing import Any

from livekit import rtc

logger = logging.getLogger("hume-tracker")


class HumeEmotionTracker:
    """Maintain rolling vocal emotion state for one interview session."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._current_emotions: dict = {}
        self._emotion_history: list[dict] = []
        self._recent_snapshots: deque = deque(maxlen=5)
        self._running = False
        self._task: asyncio.Task | None = None
        self._room: Any = None

    async def start(self, room: Any) -> None:
        """Start background tracking loop."""
        self._room = room
        self._running = True
        self._task = asyncio.create_task(self._streaming_loop())

    async def _streaming_loop(self) -> None:
        """Run the Hume streaming connector with safe fallback when unavailable."""
        if not self.api_key:
            logger.warning("HUME_API_KEY not set; emotion tracking disabled.")
            return

        try:
            from hume import AsyncHumeClient
            from hume.expression_measurement.stream.stream.types.config import Config
            from hume.expression_measurement.stream.stream.types.stream_models_endpoint_payload import (
                StreamModelsEndpointPayload,
            )
        except Exception as exc:  # pragma: no cover - optional dependency
            logger.warning("hume[stream] dependency unavailable: %s", exc)
            return

        client = AsyncHumeClient(api_key=self.api_key)
        while self._running:
            try:
                track = await self._wait_for_suitor_audio_track()
                if track is None:
                    await asyncio.sleep(1)
                    continue

                async with client.expression_measurement.stream.connect(
                    hume_api_key=self.api_key
                ) as socket:
                    audio_stream = rtc.AudioStream(track=track)
                    buffer = bytearray()
                    buffer_duration = 0.0
                    try:
                        async for frame_event in audio_stream:
                            if not self._running:
                                break
                            frame = frame_event.frame
                            buffer.extend(bytes(frame.data))
                            buffer_duration += float(frame.duration)

                            if buffer_duration >= 3.0:
                                wav_bytes = self._pcm_to_wav(
                                    pcm_bytes=bytes(buffer),
                                    sample_rate=frame.sample_rate,
                                    channels=frame.num_channels,
                                )
                                payload = StreamModelsEndpointPayload(
                                    data=base64.b64encode(wav_bytes).decode("utf-8"),
                                    models=Config(prosody={}),
                                )
                                await socket.send_publish(payload)
                                prediction = await socket.recv()
                                if hasattr(prediction, "model_dump"):
                                    result = prediction.model_dump()
                                elif hasattr(prediction, "dict"):
                                    result = prediction.dict()
                                else:
                                    result = {}
                                self.process_predictions(result)
                                buffer.clear()
                                buffer_duration = 0.0
                    finally:
                        await audio_stream.aclose()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("Hume stream reconnecting after error: %s", exc)
                await asyncio.sleep(2)

    async def _wait_for_suitor_audio_track(self, timeout_seconds: float = 30.0):
        """Wait until a remote suitor audio track is available in the room."""
        if self._room is None:
            return None
        waited = 0.0
        while self._running and waited < timeout_seconds:
            participants = getattr(self._room, "remote_participants", {}) or {}
            for participant in participants.values():
                identity = getattr(participant, "identity", "")
                if not identity.startswith("suitor-"):
                    continue
                pubs = getattr(participant, "track_publications", {}) or {}
                for publication in pubs.values():
                    if (
                        getattr(publication, "kind", None) == rtc.TrackKind.KIND_AUDIO
                        and getattr(publication, "track", None) is not None
                    ):
                        return publication.track
            await asyncio.sleep(1.0)
            waited += 1.0
        return None

    def _pcm_to_wav(self, pcm_bytes: bytes, sample_rate: int, channels: int) -> bytes:
        """Convert PCM bytes into WAV payload expected by Hume streaming endpoint."""
        with io.BytesIO() as buffer:
            with wave.open(buffer, "wb") as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)  # 16-bit pcm
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm_bytes)
            return buffer.getvalue()

    def process_predictions(self, result: dict | None) -> None:
        """Process raw Hume prosody predictions into interview-specific signals."""
        if not result:
            return

        prosody = result.get("prosody", {})
        predictions = prosody.get("predictions") or []
        if not predictions:
            return
        emotions = predictions[0].get("emotions") or []
        if not emotions:
            return

        scores = {entry.get("name"): entry.get("score", 0) for entry in emotions}
        now_ts = asyncio.get_running_loop().time()
        ranked = sorted(emotions, key=lambda e: e.get("score", 0), reverse=True)

        snapshot = {
            "confidence": max(
                scores.get("Confidence", 0),
                scores.get("Determination", 0),
                scores.get("Pride", 0),
            ),
            "anxiety": max(
                scores.get("Anxiety", 0),
                scores.get("Fear", 0),
                scores.get("Nervousness", 0),
                scores.get("Distress", 0),
            ),
            "enthusiasm": max(
                scores.get("Joy", 0),
                scores.get("Excitement", 0),
                scores.get("Interest", 0),
            ),
            "warmth": max(
                scores.get("Admiration", 0),
                scores.get("Love", 0),
                scores.get("Gratitude", 0),
            ),
            "amusement": scores.get("Amusement", 0),
            "discomfort": max(
                scores.get("Distress", 0),
                scores.get("Embarrassment", 0),
                scores.get("Awkwardness", 0),
            ),
            "timestamp": now_ts,
            "dominant_emotion": ranked[0].get("name", "Unknown"),
            "dominant_score": ranked[0].get("score", 0),
            "raw_top_5": [
                {"name": e.get("name", "Unknown"), "score": round(e.get("score", 0), 3)}
                for e in ranked[:5]
            ],
        }

        self._current_emotions = snapshot
        self._recent_snapshots.append(snapshot)
        self._emotion_history.append(snapshot)

    def get_current_state(self) -> dict:
        """Return latest emotion snapshot."""
        return self._current_emotions or {}

    def get_emotion_summary(self) -> str:
        """Return short summary suitable for LLM tool output."""
        state = self._current_emotions
        if not state:
            return "No emotion data available yet."

        parts: list[str] = []
        if state.get("anxiety", 0) > 0.5:
            parts.append("The Suitor sounds anxious or nervous")
        if state.get("confidence", 0) > 0.6:
            parts.append("The Suitor sounds confident")
        if state.get("enthusiasm", 0) > 0.5:
            parts.append("The Suitor sounds enthusiastic and engaged")
        if state.get("amusement", 0) > 0.4:
            parts.append("The Suitor seems amused or is laughing")
        if state.get("warmth", 0) > 0.4:
            parts.append("The Suitor is expressing warmth or admiration")
        if state.get("discomfort", 0) > 0.5:
            parts.append("The Suitor seems uncomfortable or embarrassed")

        if not parts:
            parts.append(
                f"The Suitor's dominant vocal tone is {state.get('dominant_emotion', 'neutral')}"
            )
        return ". ".join(parts) + "."

    def get_tts_instruction(self) -> str:
        """Return dynamic Hume TTS acting instruction."""
        state = self._current_emotions
        if not state:
            return "Speak in a warm, friendly, and confident tone."
        if state.get("anxiety", 0) > 0.5:
            return (
                "Speak in a warm, calm, reassuring tone. Be gentle but still engaging."
            )
        if state.get("discomfort", 0) > 0.5:
            return "Speak gently and with empathy. Use a softer, encouraging tone."
        if state.get("enthusiasm", 0) > 0.5 and state.get("confidence", 0) > 0.4:
            return "Match their energy with enthusiasm, playfulness, and a hint of challenge."
        if state.get("confidence", 0) > 0.6:
            return "Speak with confident, slightly teasing energy."
        if state.get("amusement", 0) > 0.4:
            return "Speak with warmth and a hint of humor."
        if state.get("warmth", 0) > 0.4:
            return "Respond with genuine warmth and openness."
        return "Speak in a friendly, engaging, naturally curious tone."

    def get_full_timeline(self) -> list[dict]:
        """Return all captured snapshots."""
        return self._emotion_history

    async def stop(self) -> None:
        """Stop background loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
