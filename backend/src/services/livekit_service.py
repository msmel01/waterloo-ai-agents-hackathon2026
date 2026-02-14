"""LiveKit room and token management for session orchestration."""

from __future__ import annotations

from typing import Any

try:
    from livekit.api import AccessToken, LiveKitAPI, VideoGrants
except Exception:  # pragma: no cover - optional dependency guard
    AccessToken = None  # type: ignore[assignment]
    LiveKitAPI = None  # type: ignore[assignment]
    VideoGrants = None  # type: ignore[assignment]


class LiveKitService:
    """Manage LiveKit rooms and participant tokens from the FastAPI backend."""

    def __init__(self, api_key: str, api_secret: str, url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.url = url
        self._api = (
            LiveKitAPI(url=url, api_key=api_key, api_secret=api_secret)
            if LiveKitAPI
            else None
        )

    def _require_sdk(self) -> None:
        if not self._api or not AccessToken or not VideoGrants:
            raise RuntimeError(
                "LiveKit SDK is not available. Install `livekit-api` and "
                "`livekit-agents` dependencies."
            )

    async def create_room(
        self,
        room_name: str,
        max_participants: int = 3,
        metadata: str | None = None,
    ) -> dict[str, Any]:
        """Create a LiveKit room used by one interview session."""
        self._require_sdk()
        try:
            room = await self._api.room.create_room(  # type: ignore[union-attr]
                name=room_name,
                empty_timeout=300,
                max_participants=max_participants,
                metadata=metadata,
            )
        except TypeError:
            # Compatibility path for SDK versions expecting a request object.
            from livekit.api import CreateRoomRequest

            room = await self._api.room.create_room(  # type: ignore[union-attr]
                CreateRoomRequest(
                    name=room_name,
                    empty_timeout=300,
                    max_participants=max_participants,
                    metadata=metadata,
                )
            )
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
        try:
            await self._api.room.delete_room(room_name)  # type: ignore[union-attr]
        except Exception:
            # Room may already be cleaned up by timeout/egress flows.
            return

    async def close(self) -> None:
        """Close API client resources if the SDK provides an async close hook."""
        if self._api and hasattr(self._api, "aclose"):
            await self._api.aclose()
