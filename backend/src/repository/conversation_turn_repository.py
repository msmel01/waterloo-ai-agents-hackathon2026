"""Repository for conversation turns."""

import uuid
from typing import Any, Callable

from sqlmodel import select

from src.models.conversation_turn_model import ConversationTurnDb
from src.repository.base_repository import BaseRepository


class ConversationTurnRepository(BaseRepository):
    """Data access helpers for conversation turns."""

    def __init__(self, session_factory: Callable[..., Any]):
        super().__init__(session_factory, ConversationTurnDb)

    async def find_by_session_id(
        self, session_id: uuid.UUID
    ) -> list[ConversationTurnDb]:
        """List transcript turns in order for one session."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model)
                .where(self.model.session_id == session_id)
                .order_by(self.model.turn_index.asc(), self.model.created_at.asc())
            )
            return list(result.scalars().all())
