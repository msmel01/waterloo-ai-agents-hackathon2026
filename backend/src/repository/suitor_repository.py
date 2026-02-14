"""Repository for suitors."""

from typing import Any, Callable

from sqlmodel import delete, select

from src.models.suitor_model import SuitorDb
from src.repository.base_repository import BaseRepository


class SuitorRepository(BaseRepository):
    """CRUD repository for suitors."""

    def __init__(self, session_factory: Callable[..., Any]):
        super().__init__(session_factory, SuitorDb)

    async def find_by_clerk_id(self, clerk_user_id: str) -> SuitorDb | None:
        """Find a suitor by Clerk user ID."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.clerk_user_id == clerk_user_id)
            )
            return result.scalars().first()

    async def update_by_clerk_id(
        self, clerk_user_id: str, data: dict
    ) -> SuitorDb | None:
        """Update suitor fields by Clerk user ID."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.clerk_user_id == clerk_user_id)
            )
            suitor = result.scalars().first()
            if not suitor:
                return None

            for key, value in data.items():
                setattr(suitor, key, value)

            session.add(suitor)
            await session.commit()
            await session.refresh(suitor)
            return suitor

    async def delete_by_clerk_id(self, clerk_user_id: str) -> bool:
        """Delete suitor by Clerk user ID."""
        async with self.session_factory() as session:
            result = await session.execute(
                delete(self.model).where(self.model.clerk_user_id == clerk_user_id)
            )
            await session.commit()
            return bool(result.rowcount)
