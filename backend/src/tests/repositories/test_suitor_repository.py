"""Unit tests for SuitorRepository."""

from src.models.suitor_model import SuitorDb
from src.repository.suitor_repository import SuitorRepository


def test_suitor_repository_uses_suitor_model(session_factory):
    repo = SuitorRepository(session_factory=session_factory)
    assert repo.model is SuitorDb
