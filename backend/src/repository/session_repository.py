"""Repository for interview sessions."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from sqlalchemy import func
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
                select(self.model)
                .where(
                    self.model.suitor_id == suitor_id,
                    self.model.status.in_(
                        [SessionStatus.PENDING, SessionStatus.IN_PROGRESS]
                    ),
                )
                .order_by(self.model.created_at.desc())
            )
            return result.scalars().first()

    async def count_today_by_suitor(self, suitor_id: uuid.UUID) -> int:
        """Count sessions created in the last UTC day window for one suitor."""
        async with self.session_factory() as session:
            day_start = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)
            result = await session.execute(
                select(func.count(self.model.id)).where(
                    self.model.suitor_id == suitor_id,
                    self.model.created_at >= day_start,
                    self.model.created_at < day_end,
                )
            )
            count = result.scalar_one_or_none()
            return int(count or 0)

    async def count_active_by_heart(self, heart_id: uuid.UUID) -> int:
        """Count active sessions for one heart (pending/in-progress)."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(func.count(self.model.id)).where(
                    self.model.heart_id == heart_id,
                    self.model.status.in_(
                        [SessionStatus.PENDING, SessionStatus.IN_PROGRESS]
                    ),
                )
            )
            count = result.scalar_one_or_none()
            return int(count or 0)

    async def find_by_suitor(
        self, suitor_id: uuid.UUID, *, limit: int = 20
    ) -> list[SessionDb]:
        """Get recent sessions for one suitor, newest first."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model)
                .where(self.model.suitor_id == suitor_id)
                .order_by(self.model.created_at.desc())
                .limit(limit)
            )
            return list(result.scalars().all())

    async def find_stale_pending(self, older_than: datetime) -> list[SessionDb]:
        """Find pending sessions older than cutoff timestamp."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(
                    self.model.status == SessionStatus.PENDING,
                    self.model.created_at < older_than,
                )
            )
            return list(result.scalars().all())

    async def find_stale_in_progress(self, older_than: datetime) -> list[SessionDb]:
        """Find in-progress sessions with stale started_at timestamps."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(self.model).where(
                    self.model.status == SessionStatus.IN_PROGRESS,
                    self.model.started_at.is_not(None),
                    self.model.started_at < older_than,
                )
            )
            return list(result.scalars().all())
