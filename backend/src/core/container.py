import os

from dependency_injector import containers, providers

from src.core.config import Config, get_config
from src.core.database import Database
from src.repository.booking_repository import BookingRepository
from src.repository.conversation_turn_repository import ConversationTurnRepository
from src.repository.heart_repository import HeartRepository
from src.repository.score_repository import ScoreRepository
from src.repository.screening_question_repository import ScreeningQuestionRepository
from src.repository.session_repository import SessionRepository
from src.repository.suitor_repository import SuitorRepository
from src.repository.user_repository import UserRepository
from src.services.chat_service import ChatService
from src.services.user_service import UserService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "src.dependencies",
            "src.api.v1.endpoints.auth",
            "src.api.v1.endpoints.admin",
            "src.api.v1.endpoints.public",
            "src.api.v1.endpoints.suitors",
            "src.api.v1.endpoints.sessions",
            "src.api.v1.endpoints.bookings",
        ]
    )

    config: Config = providers.Singleton(get_config)
    os.environ["SMALLEST_API_KEY"] = config.SMALLEST_AI_API_KEY.get_secret_value()

    database = providers.Singleton(Database, config=config)

    user_repository = providers.Factory(
        UserRepository,
        session_factory=database.provided.session,
    )

    heart_repository = providers.Factory(
        HeartRepository,
        session_factory=database.provided.session,
    )

    screening_question_repository = providers.Factory(
        ScreeningQuestionRepository,
        session_factory=database.provided.session,
    )

    suitor_repository = providers.Factory(
        SuitorRepository,
        session_factory=database.provided.session,
    )

    session_repository = providers.Factory(
        SessionRepository,
        session_factory=database.provided.session,
    )

    conversation_turn_repository = providers.Factory(
        ConversationTurnRepository,
        session_factory=database.provided.session,
    )

    score_repository = providers.Factory(
        ScoreRepository,
        session_factory=database.provided.session,
    )

    booking_repository = providers.Factory(
        BookingRepository,
        session_factory=database.provided.session,
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
    )

    chat_service = providers.Factory(
        ChatService,
        config=config,
    )
