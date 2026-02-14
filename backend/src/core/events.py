import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.logging_conf import configure_logging
from src.services.calcom_service import CalcomService
from src.services.config_loader import HeartConfigLoader
from src.services.tavus_service import TavusService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()

    # Initialize container resources
    if hasattr(app.state, "container"):
        app.state.container.init_resources()
        logger.info("Container resources initialized")

    loader = HeartConfigLoader()
    loaded_config = loader.load()
    logger.info(
        "Heart config loaded for '%s' (slug: %s)",
        loaded_config.profile.display_name,
        loaded_config.shareable_slug,
    )

    database = app.state.container.database()
    async with database.session() as db:
        heart = await loader.seed_database(db)
        app.state.heart_config = loaded_config
        app.state.heart_id = heart.id
        logger.info("Heart seeded in database with id=%s", heart.id)

    # Validate external services without blocking startup on failures.
    try:
        calcom = CalcomService(
            loaded_config.calendar.calcom_api_key,
            loaded_config.calendar.calcom_event_type_id,
        )
        is_valid = await calcom.validate_connection()
        if is_valid:
            logger.info(
                "cal.com connected (event_type_id=%s)",
                loaded_config.calendar.calcom_event_type_id,
            )
        else:
            logger.warning(
                "cal.com connection failed (event_type_id=%s)",
                loaded_config.calendar.calcom_event_type_id,
            )
    except Exception as exc:
        logger.warning("cal.com validation failed: %s", exc)

    if heart.tavus_avatar_id:
        try:
            tavus = TavusService(loaded_config.avatar.tavus_api_key)
            status_payload = await tavus.get_replica(heart.tavus_avatar_id)
            logger.info(
                "Tavus replica %s status: %s",
                heart.tavus_avatar_id,
                status_payload.get("status", "unknown"),
            )
        except Exception as exc:
            logger.warning("Tavus status check failed: %s", exc)
    else:
        logger.info(
            "Tavus replica not initialized. Run POST /api/v1/admin/avatar/create"
        )

    logger.info("Startup event completed")

    yield

    # Shutdown container resources
    if hasattr(app.state, "container"):
        app.state.container.shutdown_resources()
        logger.info("Container resources shutdown")

    logger.info("Shutdown event completed")
