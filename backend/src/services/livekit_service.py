"""LiveKit room and token management for session orchestration."""

from __future__ import annotations

from typing import Any

try:
    from livekit.api import (
        AccessToken,
        CreateAgentDispatchRequest,
        LiveKitAPI,
        VideoGrants,
    )
except ImportError:  # pragma: no cover - optional dependency guard
    AccessToken = None  # type: ignore[assignment]
    CreateAgentDispatchRequest = None  # type: ignore[assignment]
    LiveKitAPI = None  # type: ignore[assignment]
    VideoGrants = None  # type: ignore[assignment]


class LiveKitService:
    """Manage LiveKit rooms and participant tokens from the FastAPI backend."""

    def __init__(self, api_key: str, api_secret: str, url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.url = url

    def _require_sdk(self) -> None:
        if not LiveKitAPI or not AccessToken or not VideoGrants:
            raise RuntimeError(
                "LiveKit SDK is not available. Install `livekit-api` and "
                "`livekit-agents` dependencies."
            )

    def _new_api(self):
        """Create a LiveKitAPI client in an async context."""
        self._require_sdk()
        return LiveKitAPI(
            url=self.url, api_key=self.api_key, api_secret=self.api_secret
        )

    async def create_room(
        self,
        room_name: str,
        max_participants: int = 3,
        metadata: str | None = None,
    ) -> dict[str, Any]:
        """Create a LiveKit room used by one interview session."""
        self._require_sdk()
        api = self._new_api()
        try:
            try:
                room = await api.room.create_room(
                    name=room_name,
                    empty_timeout=300,
                    max_participants=max_participants,
                    metadata=metadata,
                )
            except TypeError:
                # Compatibility path for SDK versions expecting a request object.
                from livekit.api import CreateRoomRequest

                room = await api.room.create_room(
                    CreateRoomRequest(
                        name=room_name,
                        empty_timeout=300,
                        max_participants=max_participants,
                        metadata=metadata,
                    )
                )
        finally:
            await api.aclose()
        return {"name": room.name, "sid": room.sid}

    def generate_suitor_token(
        self, room_name: str, suitor_id: str, suitor_name: str
    ) -> str:
        """Generate a room-join token for one authenticated suitor."""
        self._require_sdk()
        token = AccessToken(self.api_key, self.api_secret)
        token.with_identity(f"suitor-{suitor_id}")
        token.with_name(suitor_name)
        token.with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        return token.to_jwt()

    async def delete_room(self, room_name: str) -> None:
        """Delete a LiveKit room when a session is fully complete."""
        self._require_sdk()
        api = self._new_api()
        try:
            await api.room.delete_room(room_name)
        except Exception:
            # Room may already be cleaned up by timeout/egress flows.
            return
        finally:
            await api.aclose()

    async def close(self) -> None:
        """Close API client resources if the SDK provides an async close hook."""
        # LiveKitAPI is created per-call in async methods, so this is a no-op.
        return

    async def create_agent_dispatch(
        self, room_name: str, agent_name: str, metadata: str | None = None
    ) -> dict[str, Any]:
        """Explicitly dispatch an agent worker into a room."""
        self._require_sdk()
        if not CreateAgentDispatchRequest:
            raise RuntimeError("CreateAgentDispatchRequest unavailable in livekit-api")
        api = self._new_api()
        try:
            dispatch = await api.agent_dispatch.create_dispatch(
                CreateAgentDispatchRequest(
                    room=room_name,
                    agent_name=agent_name,
                    metadata=metadata or "",
                )
            )
        finally:
            await api.aclose()
        return {
            "id": dispatch.id,
            "agent_name": dispatch.agent_name,
            "room": dispatch.room,
        }
