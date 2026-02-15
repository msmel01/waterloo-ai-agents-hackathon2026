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

    async def create(self, score_data: dict[str, Any]) -> ScoreDb:
        """Create and persist a score record."""
        score = self.model(**score_data)
        return await super().create(score)

    async def find_by_session_id(self, session_id: uuid.UUID) -> ScoreDb | None:
        """Get score for one session."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.session_id == session_id)
            )
            return result.scalars().first()

    async def exists_for_session(self, session_id: uuid.UUID) -> bool:
        """Check if a score record already exists for the session."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model.id).where(self.model.session_id == session_id)
            )
            return result.scalar_one_or_none() is not None
