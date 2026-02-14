"""Repository for scores."""

import uuid
from typing import Any, Callable

from sqlmodel import select

from src.models.score_model import ScoreDb
from src.repository.base_repository import BaseRepository


class ScoreRepository(BaseRepository):
    """Data access helpers for session scores."""

    def __init__(self, session_factory: Callable[..., Any]):
        super().__init__(session_factory, ScoreDb)

    async def find_by_session_id(self, session_id: uuid.UUID) -> ScoreDb | None:
        """Get score for one session."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.session_id == session_id)
            )
            return result.scalars().first()
