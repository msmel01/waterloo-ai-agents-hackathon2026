"""Valentine Hotline LiveKit Agent server.

Run:
    python -m livekit.agents dev agent.main
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
from agent.interview_agent import InterviewAgent
from agent.prompt_builder import build_system_prompt
from agent.session_manager import SessionManager

logger = logging.getLogger("valentine-agent")

try:
    from livekit.agents import AgentServer, AgentSession, JobContext, RoomOutputOptions
    from livekit.plugins import silero, smallestai, tavus
except Exception as exc:  # pragma: no cover - dependency guard
    AgentServer = None  # type: ignore[assignment]
    AgentSession = None  # type: ignore[assignment]
    JobContext = object  # type: ignore[assignment]
    RoomOutputOptions = None  # type: ignore[assignment]
    silero = None  # type: ignore[assignment]
    smallestai = None  # type: ignore[assignment]
    tavus = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

server = AgentServer() if AgentServer else None


if server:

    @server.rtc_session()
    async def entrypoint(ctx: JobContext):  # type: ignore[misc]
        """Handle one room interview session lifecycle."""
        await ctx.connect()

        room_name = ctx.room.name
        session_id = room_name.removeprefix("session-")
        try:
            uuid.UUID(session_id)
        except ValueError:
            logger.error("Invalid room name/session id: %s", room_name)
            return

        heart_config = await get_heart_config()
        session_data = await get_session_by_room(session_id)
        if not session_data:
            logger.error("No DB session found for room %s", room_name)
            return

        prompt = build_system_prompt(
            heart_config=heart_config,
            suitor_name=session_data["suitor_name"],
        )
        session_mgr = SessionManager(
            session_id=session_id,
            questions=heart_config["screening_questions"],
            max_duration_seconds=600,
        )
        interview_agent = InterviewAgent(
            instructions=prompt,
            session_manager=session_mgr,
        )

        session = AgentSession(
            vad=silero.VAD.load(),
            stt=smallestai.STT(model="pulse", language="en"),
            llm=smallestai.LLM(model="electron"),
            tts=smallestai.TTS(model="lightning", voice="emily", sample_rate=24000),
            allow_interruptions=True,
            min_endpointing_delay=0.5,
            max_endpointing_delay=3.0,
        )

        @session.on("user_input_transcribed")
        async def on_user_speech(event):
            text = getattr(event, "text", "").strip()
            if text:
                session_mgr.add_transcript_entry(speaker="suitor", text=text)
                if session_mgr.ramble_detector.should_interrupt():
                    session_mgr.add_transcript_entry(
                        speaker="avatar",
                        text="I appreciate the detail, but let's keep moving.",
                    )

        @session.on("agent_speech_committed")
        async def on_agent_speech(event):
            text = getattr(event, "text", "").strip()
            if text:
                session_mgr.add_transcript_entry(speaker="avatar", text=text)

        @session.on("close")
        async def on_session_close():
            if session_mgr.end_reason is None:
                session_mgr.end("session_closed")
            data = session_mgr.get_session_data()
            await save_conversation_data(session_id, data)
            logger.info(
                "Session %s completed. duration=%.0fs turns=%s",
                session_id,
                data["duration_seconds"],
                len(data["turns"]),
            )

        @ctx.room.on("participant_disconnected")
        async def on_participant_disconnected(participant):
            identity = getattr(participant, "identity", "")
            if identity.startswith("suitor-"):
                logger.warning("Suitor disconnected in session %s", session_id)
                session_mgr.end("suitor_disconnected")
                await on_session_close()

        await update_session_status(session_id, "in_progress")

        if heart_config.get("tavus_replica_id"):
            avatar_session = tavus.AvatarSession(
                replica_id=heart_config["tavus_replica_id"],
                persona_id=heart_config.get("tavus_persona_id"),
            )
            await avatar_session.start(session, room=ctx.room)

        await session.start(
            room=ctx.room,
            agent=interview_agent,
            room_output_options=RoomOutputOptions(audio_enabled=False),
        )

        while session_mgr.end_reason is None and not session_mgr.is_overtime():
            await asyncio.sleep(1)
        if session_mgr.end_reason is None:
            session_mgr.end("max_duration_reached")

else:

    def _missing_server(*_args, **_kwargs):  # pragma: no cover
        raise RuntimeError(
            "LiveKit agent dependencies are missing. Install livekit-agents v1.x plugins."
        ) from _IMPORT_ERROR
