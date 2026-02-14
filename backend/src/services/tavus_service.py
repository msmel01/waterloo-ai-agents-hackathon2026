"""Tavus API service."""

from __future__ import annotations

import httpx


class TavusService:
    """Integrates with Tavus API to create and manage avatar replicas."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://tavusapi.com/v2"
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
        }

    async def create_replica(self, replica_name: str, train_video_url: str) -> dict:
        """Create a Tavus replica from a training video URL."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/replicas",
                headers=self.headers,
                json={
                    "train_video_url": train_video_url,
                    "replica_name": replica_name,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def get_replica(self, replica_id: str) -> dict:
        """Fetch Tavus replica status/details."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/replicas/{replica_id}",
                headers=self.headers,
                timeout=15.0,
            )
            response.raise_for_status()
            return response.json()

    async def create_conversation(
        self,
        replica_id: str,
        conversation_name: str,
        custom_greeting: str | None = None,
        max_call_duration: int = 600,
        enable_recording: bool = True,
    ) -> dict:
        """Create Tavus conversation instance for interview sessions (used in M3)."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/conversations",
                headers=self.headers,
                json={
                    "replica_id": replica_id,
                    "conversation_name": conversation_name,
                    "custom_greeting": custom_greeting,
                    "properties": {
                        "max_call_duration": max_call_duration,
                        "enable_recording": enable_recording,
                        "language": "english",
                    },
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
