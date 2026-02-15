"""Structured logging and optional Sentry bootstrapping."""

from __future__ import annotations

import logging

from src.core.config import config


def configure_structlog() -> None:
    """Configure structlog when installed, otherwise keep stdlib logging."""
    try:
        import structlog
    except Exception:  # pragma: no cover - optional dependency
        return

    renderer = (
        structlog.dev.ConsoleRenderer()
        if bool(config.DEBUG)
        else structlog.processors.JSONRenderer()
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def configure_sentry() -> None:
    """Initialize Sentry if SENTRY_DSN is configured and package is available."""
    if not config.SENTRY_DSN:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    except Exception:  # pragma: no cover - optional dependency
        logging.getLogger(__name__).warning(
            "SENTRY_DSN is set but sentry-sdk is not installed."
        )
        return

    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=0.1,
        environment=(config.APP_ENV or config.ENV.value),
    )
