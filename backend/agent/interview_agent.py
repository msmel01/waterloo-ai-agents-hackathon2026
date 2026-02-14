"""Interview agent logic and callable tools."""

from __future__ import annotations

try:
    from livekit.agents import Agent, RunContext, function_tool
except Exception:  # pragma: no cover - optional dependency guard
    Agent = object  # type: ignore[assignment]
    RunContext = object  # type: ignore[assignment]

    def function_tool(fn):  # type: ignore[misc]
        return fn


from agent.hume_tracker import HumeEmotionTracker
from agent.session_manager import SessionManager


class InterviewAgent(Agent):
    """Persona-driven dating interview agent."""

    def __init__(
        self,
        instructions: str,
        session_manager: SessionManager,
        hume_tracker: HumeEmotionTracker,
        **kwargs,
    ):
        super().__init__(instructions=instructions, **kwargs)
        self.session_mgr = session_manager
        self.hume_tracker = hume_tracker

    @function_tool
    async def get_next_question(self, context: RunContext) -> str:
        """Return the next screening question instruction for the LLM."""
        _ = context
        question = self.session_mgr.get_next_question()
        if question is None:
            return "ALL_QUESTIONS_COMPLETE — wrap up the conversation naturally."
        return (
            "Ask this question next in your own style (do not read verbatim): "
            f"{question['text']}"
        )

    @function_tool
    async def record_suitor_response(
        self, context: RunContext, question_index: int, response_summary: str
    ) -> str:
        """Record one summarized suitor answer with latest emotion snapshot."""
        _ = context
        emotions = self.hume_tracker.get_latest_emotions()
        self.session_mgr.record_response(question_index, response_summary, emotions)
        return "Response recorded. Move to follow-up or next question."

    @function_tool
    async def end_interview(self, context: RunContext, reason: str) -> str:
        """Mark interview as ended and direct the model to give closing message."""
        _ = context
        self.session_mgr.end(reason)
        return "Interview ending. Say a warm goodbye and tell them results arrive soon."
