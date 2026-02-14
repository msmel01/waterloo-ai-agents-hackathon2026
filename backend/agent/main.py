"""Valentine Hotline LiveKit Agent server entrypoint.

Run in development:
    python -m livekit.agents dev agent.main
Run in production:
    python -m livekit.agents start agent.main
"""

from __future__ import annotations

import asyncio
import logging
import uuid

from agent.db import (
    get_heart_config,
    get_session_by_room,
    save_conversation_data,
    update_session_status,
)
from agent.hume_tracker import HumeEmotionTracker
from agent.interview_agent import InterviewAgent
from agent.prompt_builder import build_system_prompt
from agent.session_manager import SessionManager
from src.core.config import config

logger = logging.getLogger(__name__)

try:
    from livekit.agents import AgentServer, AgentSession, JobContext, RoomOutputOptions
    from livekit.plugins import deepgram, silero, smallestai, tavus
except Exception as exc:  # pragma: no cover - runtime dependency guard
    AgentSession = None  # type: ignore[assignment]
    AgentServer = None  # type: ignore[assignment]
    JobContext = object  # type: ignore[assignment]
    RoomOutputOptions = None  # type: ignore[assignment]
    deepgram = None  # type: ignore[assignment]
    silero = None  # type: ignore[assignment]
    smallestai = None  # type: ignore[assignment]
    tavus = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

if AgentServer:
    server = AgentServer()
else:  # pragma: no cover
    server = None


if server:

    @server.rtc_session()
    async def entrypoint(ctx: JobContext):  # type: ignore[misc]
        """Handle one interview room session."""
        await ctx.connect()

        room_name = ctx.room.name
        if not room_name.startswith("session-"):
            logger.error("Invalid room name format: %s", room_name)
            return
        session_id = room_name.removeprefix("session-")
        try:
            uuid.UUID(session_id)
        except ValueError:
            logger.error("Invalid session UUID in room name: %s", room_name)
            return

        heart_config = await get_heart_config()
        session_data = await get_session_by_room(session_id)
        if not session_data:
            logger.error("No session found for room=%s", room_name)
            return

        instructions = build_system_prompt(
            heart_config=heart_config,
            suitor_name=session_data["suitor_name"],
        )
        session_mgr = SessionManager(
            session_id=session_id,
            questions=heart_config["screening_questions"],
            max_duration_seconds=600,
        )
        hume_tracker = HumeEmotionTracker(
            api_key=(
                config.HUME_API_KEY.get_secret_value() if config.HUME_API_KEY else ""
            ),
            session_id=session_id,
        )

        agent = InterviewAgent(
            instructions=instructions,
            session_manager=session_mgr,
            hume_tracker=hume_tracker,
        )

        # SmallestAI may not expose an LLM plugin in some installs; use OpenAI-compatible
        # fallback model endpoint if needed by your deployment.
        llm_component = smallestai.LLM(model="smallest-llm-model")
        session = AgentSession(
            vad=silero.VAD.load(),
            stt=deepgram.STT(model="nova-3", language="en"),
            llm=llm_component,
            tts=smallestai.TTS(model="lightning", voice="emily", sample_rate=24000),
            allow_interruptions=True,
            min_endpointing_delay=0.5,
            max_endpointing_delay=3.0,
        )

        @session.on("user_input_transcribed")
        def on_user_input(event):
            text = getattr(event, "text", "").strip()
            if not text:
                return
            session_mgr.add_transcript_entry(
                speaker="suitor",
                text=text,
                emotions=hume_tracker.get_latest_emotions(),
            )
            if session_mgr.ramble_detector.should_interrupt():
                # Nudge model behavior via transcript marker for next response turn.
                session_mgr.add_transcript_entry(
                    speaker="avatar",
                    text="Alright, I get the picture. Let me move us forward.",
                )

        @session.on("agent_speech_committed")
        def on_agent_output(event):
            text = getattr(event, "text", "").strip()
            if text:
                session_mgr.add_transcript_entry(speaker="avatar", text=text)

        @session.on("close")
        async def on_close():
            await hume_tracker.stop()
            if session_mgr.end_reason is None:
                session_mgr.end("session_closed")
            session_payload = session_mgr.get_session_data()
            session_payload["emotion_timeline"] = hume_tracker.get_emotion_timeline()
            await save_conversation_data(session_id, session_payload)
            logger.info("Session %s persisted after close event", session_id)

        @ctx.room.on("participant_disconnected")
        async def on_participant_disconnected(participant):
            identity = getattr(participant, "identity", "")
            if identity.startswith("suitor-"):
                logger.warning("Suitor disconnected for session=%s", session_id)
                session_mgr.end("suitor_disconnected")
                await on_close()

        await update_session_status(session_id, "in_progress")

        if heart_config.get("tavus_replica_id"):
            avatar = tavus.AvatarSession(replica_id=heart_config["tavus_replica_id"])
            await avatar.start(session, room=ctx.room)

        await hume_tracker.start(ctx.room)
        await session.start(
            room=ctx.room,
            agent=agent,
            room_output_options=RoomOutputOptions(audio_enabled=False),
        )

        # Session runs until room/session closes.
        while session_mgr.end_reason is None and not session_mgr.is_overtime():
            await asyncio.sleep(1)
        if session_mgr.end_reason is None:
            session_mgr.end("max_duration_reached")

else:

    def _missing_server(*_args, **_kwargs):  # pragma: no cover
        raise RuntimeError(
            "LiveKit agent dependencies are missing. "
            "Install livekit-agents plugins first."
        ) from _IMPORT_ERROR
