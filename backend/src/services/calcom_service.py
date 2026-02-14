"""cal.com API service."""

from __future__ import annotations

import httpx


class CalcomService:
    """Integrates with cal.com v2 API for availability and booking."""

    def __init__(self, api_key: str, event_type_id: str):
        self.api_key = api_key
        self.event_type_id = event_type_id
        self.base_url = "https://api.cal.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "cal-api-version": "2024-08-13",
        }

    async def validate_connection(self) -> bool:
        """Validate API key and configured event type."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/event-types/{self.event_type_id}",
                    headers=self.headers,
                    timeout=10.0,
                )
                return response.status_code == 200
        except Exception:
            return False

    async def get_available_slots(self, start_date: str, end_date: str) -> list[dict]:
        """Fetch available slots for configured event type."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/slots/available",
                headers=self.headers,
                params={
                    "eventTypeId": self.event_type_id,
                    "startTime": start_date,
                    "endTime": end_date,
                },
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("slots", [])

    async def create_booking(
        self,
        slot_start: str,
        attendee_name: str,
        attendee_email: str,
        notes: str | None = None,
    ) -> dict:
        """Create cal.com booking for a suitor (used in M6)."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bookings",
                headers=self.headers,
                json={
                    "eventTypeId": int(self.event_type_id),
                    "start": slot_start,
                    "attendee": {
                        "name": attendee_name,
                        "email": attendee_email,
                    },
                    "metadata": {
                        "source": "valentine-hotline",
                        "notes": notes or "",
                    },
                },
                timeout=15.0,
            )
            response.raise_for_status()
            return response.json()
