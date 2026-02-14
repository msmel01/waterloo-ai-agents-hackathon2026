"""Repository for interview sessions."""

import uuid
from typing import Any, Callable

from sqlmodel import select

from src.models.domain_enums import SessionStatus
from src.models.session_model import SessionDb
from src.repository.base_repository import BaseRepository


class SessionRepository(BaseRepository):
    """Data access helpers for sessions."""

    def __init__(self, session_factory: Callable[..., Any]):
        super().__init__(session_factory, SessionDb)

    async def find_by_heart_id(self, heart_id: uuid.UUID) -> list[SessionDb]:
        """List sessions for a heart, newest first."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model)
                .where(self.model.heart_id == heart_id)
                .order_by(self.model.created_at.desc())
            )
            return list(result.scalars().all())

    async def update_status(
        self, session_id: uuid.UUID, status: SessionStatus
    ) -> SessionDb | None:
        """Update session status."""
        async with self.session_factory() as session:
            db_obj = await session.get(self.model, session_id)
            if not db_obj:
                return None
            db_obj.status = status
            session.add(db_obj)
            await session.commit()
            await session.refresh(db_obj)
            return db_obj

    async def find_active_by_suitor_heart(
        self, suitor_id: uuid.UUID, heart_id: uuid.UUID
    ) -> SessionDb | None:
        """Find any pending/in-progress session for one suitor-heart pair."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(
                    self.model.suitor_id == suitor_id,
                    self.model.heart_id == heart_id,
                    self.model.status.in_(
                        [SessionStatus.PENDING, SessionStatus.IN_PROGRESS]
                    ),
                )
            )
            return result.scalars().first()

    async def find_active_by_suitor(self, suitor_id: uuid.UUID) -> SessionDb | None:
        """Find any active pending/in-progress session for one suitor."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(
                    self.model.suitor_id == suitor_id,
                    self.model.status.in_(
                        [SessionStatus.PENDING, SessionStatus.IN_PROGRESS]
                    ),
                )
            )
            return result.scalars().first()
