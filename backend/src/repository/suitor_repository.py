"""Repository for suitors."""

from typing import Any, Callable

from src.models.suitor_model import SuitorDb
from src.repository.base_repository import BaseRepository


class SuitorRepository(BaseRepository):
    """CRUD repository for suitors."""

    def __init__(self, session_factory: Callable[..., Any]):
        super().__init__(session_factory, SuitorDb)
