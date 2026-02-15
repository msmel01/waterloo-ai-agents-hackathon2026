"""Valentine Hotline LiveKit Agent server (voice-only, emotion-aware)."""

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
from src.core.config import LLMProvider, TTSProvider, config

logger = logging.getLogger("valentine-agent")

try:
    from livekit.agents import AgentServer, AgentSession, JobContext
    from livekit.plugins import silero, smallestai
except Exception as exc:  # pragma: no cover - dependency guard
    AgentServer = None  # type: ignore[assignment]
    AgentSession = None  # type: ignore[assignment]
    JobContext = object  # type: ignore[assignment]
    silero = None  # type: ignore[assignment]
    smallestai = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None
    try:
        from livekit.plugins import deepgram
    except Exception:  # pragma: no cover - optional plugin
        deepgram = None  # type: ignore[assignment]
    try:
        from livekit.plugins import hume
    except Exception:  # pragma: no cover - optional plugin
        hume = None  # type: ignore[assignment]
    try:
        from livekit.plugins import openai as lk_openai
    except Exception:  # pragma: no cover - optional plugin
        lk_openai = None  # type: ignore[assignment]

server = AgentServer() if AgentServer else None
AGENT_NAME = "valentine-interview-agent"


def _build_stt():
    """Prefer SmallestAI STT when available; otherwise use Deepgram."""
    if smallestai is not None and hasattr(smallestai, "STT"):
        return smallestai.STT(model="pulse", language="en")
    if deepgram is None:
        raise RuntimeError(
            "No STT provider available. Install `livekit-plugins-deepgram` or "
            "upgrade `livekit-plugins-smallestai` to a version exposing STT."
        )
    if not config.DEEPGRAM_API_KEY:
        raise RuntimeError(
            "DEEPGRAM_API_KEY is required for STT fallback because the installed "
            "SmallestAI plugin does not expose STT."
        )
    return deepgram.STT(
        model="nova-3",
        language="en-US",
        api_key=config.DEEPGRAM_API_KEY.get_secret_value(),
    )


def _build_llm():
    """Build an LLM client with stable provider preference."""
    if smallestai is not None and hasattr(smallestai, "LLM"):
        logger.info("Using native SmallestAI LLM plugin (model=electron)")
        return smallestai.LLM(model="electron")

    if lk_openai is None:
        raise RuntimeError(
            "LLM plugin unavailable. Install `livekit-plugins-openai` or enable the "
            "`openai` extra in `livekit-agents`."
        )

    # Prefer OpenAI whenever it is configured (unless explicitly set to HuggingFace).
    if config.OPENAI_API_KEY and config.LLM_PROVIDER != LLMProvider.HUGGINGFACE:
        model_name = config.MODEL_NAME or "gpt-4o-mini"
        logger.info("Using OpenAI LLM (model=%s)", model_name)
        return lk_openai.LLM(
            model=model_name,
            api_key=config.OPENAI_API_KEY.get_secret_value(),
        )

    if config.SMALLEST_AI_API_KEY:
        logger.info(
            "Using Smallest OpenAI-compatible LLM (base_url=%s, model=%s)",
            config.SMALLEST_LLM_BASE_URL,
            config.SMALLEST_LLM_MODEL,
        )
        return lk_openai.LLM(
            model=config.SMALLEST_LLM_MODEL,
            api_key=config.SMALLEST_AI_API_KEY.get_secret_value(),
            base_url=config.SMALLEST_LLM_BASE_URL,
        )

    if config.LLM_PROVIDER == LLMProvider.HUGGINGFACE:
        raise RuntimeError(
            "LLM_PROVIDER=huggingface is not supported by the LiveKit voice runtime. "
            "Set `LLM_PROVIDER=openai` and provide `OPENAI_API_KEY`."
        )

    raise RuntimeError(
        "No LLM credentials found. Set `OPENAI_API_KEY` (preferred) or "
        "`SMALLEST_AI_API_KEY`."
    )


def _build_tts():
    """Build TTS from `TTS` env setting (`deepgram` or `smallestai`)."""
    if config.TTS == TTSProvider.DEEPGRAM:
        if deepgram is None:
            raise RuntimeError(
                "TTS=deepgram requires `livekit-plugins-deepgram` to be installed."
            )
        if not config.DEEPGRAM_API_KEY:
            raise RuntimeError("TTS=deepgram requires `DEEPGRAM_API_KEY`.")
        logger.info("Using Deepgram TTS (model=%s)", config.DEEPGRAM_TTS_MODEL)
        return deepgram.TTS(
            model=config.DEEPGRAM_TTS_MODEL,
            encoding="linear16",
            sample_rate=24000,
            api_key=config.DEEPGRAM_API_KEY.get_secret_value(),
        )

    if config.TTS == TTSProvider.SMALLESTAI:
        if smallestai is None or not hasattr(smallestai, "TTS"):
            raise RuntimeError("TTS=smallestai requires `livekit-plugins-smallestai`.")
        if not config.SMALLEST_AI_API_KEY:
            raise RuntimeError("TTS=smallestai requires `SMALLEST_AI_API_KEY`.")
        logger.info(
            "Using SmallestAI TTS (model=%s, voice_id=irisha)",
            config.SMALLEST_TTS_MODEL,
        )
        return smallestai.TTS(
            model=config.SMALLEST_TTS_MODEL,
            voice_id="irisha",
            sample_rate=24000,
            api_key=config.SMALLEST_AI_API_KEY.get_secret_value(),
        )

    raise RuntimeError(
        "Unsupported TTS provider. Set `TTS=deepgram` or `TTS=smallestai`."
    )


if server:

    @server.rtc_session(agent_name=AGENT_NAME)
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
        hume_tracker = HumeEmotionTracker(
            api_key=config.HUME_API_KEY.get_secret_value()
            if config.HUME_API_KEY
            else ""
        )
        interview_agent = InterviewAgent(
            instructions=prompt,
            session_manager=session_mgr,
            hume_tracker=hume_tracker,
        )

        session = AgentSession(
            vad=silero.VAD.load(),
            stt=_build_stt(),
            llm=_build_llm(),
            tts=_build_tts(),
            allow_interruptions=True,
            min_endpointing_delay=0.5,
            max_endpointing_delay=3.0,
        )

        already_saved = False
        save_lock = asyncio.Lock()
        closed = False
        close_lock = asyncio.Lock()

        def _spawn(coro):
            task = asyncio.create_task(coro)

            def _on_done(done_task: asyncio.Task) -> None:
                if done_task.cancelled():
                    return
                exc = done_task.exception()
                if exc:
                    logger.error("Background callback failed: %s", exc)

            task.add_done_callback(_on_done)
            return task

        async def save_once(reason: str) -> None:
            nonlocal already_saved
            async with save_lock:
                if already_saved:
                    return
                if session_mgr.end_reason is None:
                    session_mgr.end(reason)
                data = session_mgr.get_session_data()
                data["emotion_timeline"] = hume_tracker.get_full_timeline()
                await save_conversation_data(session_id, data)
                already_saved = True
                logger.info(
                    "Session %s completed. duration=%.0fs turns=%s",
                    session_id,
                    data["duration_seconds"],
                    len(data["turns"]),
                )

        async def _handle_user_speech(event):
            text = getattr(event, "text", "").strip()
            if not text:
                return
            session_mgr.add_transcript_entry(
                speaker="suitor",
                text=text,
                emotions=hume_tracker.get_current_state(),
            )
            # Hume-specific per-turn description updates are disabled because
            # runtime TTS is pinned to SmallestAI for reliability.
            if session_mgr.ramble_detector.should_interrupt():
                session_mgr.add_transcript_entry(
                    speaker="avatar",
                    text="I appreciate the detail, but let's keep moving.",
                )

        @session.on("user_input_transcribed")
        def on_user_speech(event):
            _spawn(_handle_user_speech(event))

        @session.on("agent_speech_committed")
        def on_agent_speech(event):
            text = getattr(event, "text", "").strip()
            if text:
                session_mgr.add_transcript_entry(speaker="avatar", text=text)

        async def on_close(reason: str) -> None:
            nonlocal closed
            async with close_lock:
                if closed:
                    return
                closed = True
                if session_mgr.end_reason is None:
                    session_mgr.end(reason)
            await hume_tracker.stop()
            await save_once(reason)

        @session.on("close")
        def on_session_close():
            _spawn(on_close("session_closed"))

        async def _handle_participant_disconnected(participant):
            identity = getattr(participant, "identity", "")
            if identity.startswith("suitor-"):
                logger.warning("Suitor disconnected in session %s", session_id)
                await on_close("suitor_disconnected")

        @ctx.room.on("participant_disconnected")
        def on_participant_disconnected(participant):
            _spawn(_handle_participant_disconnected(participant))

        await session.start(room=ctx.room, agent=interview_agent)
        await hume_tracker.start(ctx.room)
        await update_session_status(session_id, "in_progress")

        while session_mgr.end_reason is None and not session_mgr.is_overtime():
            await asyncio.sleep(1)
        if session_mgr.end_reason is None:
            session_mgr.end("max_duration_reached")

        try:
            final_reason = session_mgr.end_reason or "session_completed"
            await on_close(final_reason)
            maybe_aclose = getattr(session, "aclose", None)
            if callable(maybe_aclose):
                await maybe_aclose()
            else:
                maybe_close = getattr(session, "close", None)
                if callable(maybe_close):
                    result = maybe_close()
                    if asyncio.iscoroutine(result):
                        await result
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception(
                "Failed to finalize/close agent session %s cleanly: %s",
                session_id,
                exc,
            )

else:

    def _missing_server(*_args, **_kwargs):  # pragma: no cover
        raise RuntimeError(
            "LiveKit agent dependencies are missing. Install livekit-agents v1.x plugins."
        ) from _IMPORT_ERROR


if __name__ == "__main__":  # pragma: no cover - local runtime entrypoint
    if not server:
        _missing_server()
    from livekit.agents.cli.cli import run_app

    run_app(server)
