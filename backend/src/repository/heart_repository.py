"""Repository for heart records."""

import uuid
from typing import Any, Callable

from sqlmodel import delete, select

from src.models.heart_model import HeartDb
from src.repository.base_repository import BaseRepository


class HeartRepository(BaseRepository):
    """Data access helpers for hearts."""

    def __init__(self, session_factory: Callable[..., Any]):
        super().__init__(session_factory, HeartDb)

    async def find_by_slug(self, slug: str) -> HeartDb | None:
        """Find a heart by shareable slug."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.shareable_slug == slug)
            )
            return result.scalars().first()

    async def find_by_clerk_id(self, clerk_user_id: str) -> HeartDb | None:
        """Find a heart by Clerk user ID."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(self.model.clerk_user_id == clerk_user_id)
            )
            return result.scalars().first()

    async def delete_by_clerk_id(self, clerk_user_id: str) -> None:
        """Delete a heart by Clerk user ID."""
        async with self.session_factory() as session:
            await session.execute(
                delete(self.model).where(self.model.clerk_user_id == clerk_user_id)
            )
            await session.commit()

    async def read_by_id(self, id: uuid.UUID, eager: bool = False):
        """Read by UUID primary key."""
        return await super().read_by_id(id, eager=eager)
