"""arq worker entrypoint and placeholder background tasks."""

from __future__ import annotations

from arq.connections import RedisSettings

from src.core.config import config


async def score_session(ctx: dict, session_id: str) -> None:
    """Placeholder task for Claude-based session scoring."""
    _ = (ctx, session_id)


async def generate_tavus_avatar(ctx: dict, heart_id: str) -> None:
    """Placeholder task for Tavus avatar generation."""
    _ = (ctx, heart_id)


async def send_notification(ctx: dict, heart_id: str, event_type: str) -> None:
    """Placeholder task for heart notifications."""
    _ = (ctx, heart_id, event_type)


class WorkerSettings:
    """arq worker configuration."""

    redis_settings = RedisSettings.from_dsn(config.REDIS_URL)
    functions = [score_session, generate_tavus_avatar, send_notification]
    job_timeout = 300
    keep_result = 3600
