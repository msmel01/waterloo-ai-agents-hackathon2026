"""Repository for screening questions."""

import uuid
from typing import Any, Callable

from sqlmodel import select

from src.models.screening_question_model import ScreeningQuestionDb
from src.repository.base_repository import BaseRepository


class ScreeningQuestionRepository(BaseRepository):
    """Data access helpers for screening questions."""

    def __init__(self, session_factory: Callable[..., Any]):
        super().__init__(session_factory, ScreeningQuestionDb)

    async def find_by_heart_id(self, heart_id: uuid.UUID) -> list[ScreeningQuestionDb]:
        """List screening questions for a heart in order."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model)
                .where(self.model.heart_id == heart_id)
                .order_by(self.model.order_index.asc())
            )
            return list(result.scalars().all())

    async def bulk_reorder(
        self, heart_id: uuid.UUID, item_orders: list[tuple[uuid.UUID, int]]
    ) -> list[ScreeningQuestionDb]:
        """Apply bulk order_index updates and return ordered questions."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.heart_id == heart_id)
            )
            questions = {question.id: question for question in result.scalars().all()}

            for question_id, new_order in item_orders:
                question = questions.get(question_id)
                if question:
                    question.order_index = new_order
                    session.add(question)

            await session.commit()

        return await self.find_by_heart_id(heart_id)
