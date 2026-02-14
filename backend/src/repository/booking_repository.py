"""Repository for bookings."""

import uuid
from typing import Any, Callable

from sqlmodel import select

from src.models.booking_model import BookingDb
from src.repository.base_repository import BaseRepository


class BookingRepository(BaseRepository):
    """Data access helpers for bookings."""

    def __init__(self, session_factory: Callable[..., Any]):
        super().__init__(session_factory, BookingDb)

    async def find_by_session_id(self, session_id: uuid.UUID) -> BookingDb | None:
        """Get booking by session id."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.session_id == session_id)
            )
            return result.scalars().first()
