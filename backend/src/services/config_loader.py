"""Load, validate, and seed static Heart profile config from YAML."""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.heart_model import HeartDb
from src.models.screening_question_model import ScreeningQuestionDb


class ProfileConfig(BaseModel):
    """Public profile section in static Heart config."""

    display_name: str = Field(..., min_length=1, max_length=100)
    bio: str = Field(..., min_length=1, max_length=2000)
    photo_url: str | None = None
    video_url: str | None = None


class PersonaConfig(BaseModel):
    """Persona section in static Heart config."""

    traits: list[str] = Field(..., min_length=1, max_length=10)
    vibe: str = Field(..., max_length=500)
    tone: str = Field(..., max_length=500)
    humor_level: int = Field(..., ge=1, le=10)
    strictness: int = Field(..., ge=1, le=10)
    custom_instructions: str | None = Field(default=None, max_length=2000)


class ExpectationsConfig(BaseModel):
    """Expectations section in static Heart config."""

    dealbreakers: list[str] = Field(default_factory=list, max_length=20)
    green_flags: list[str] = Field(default_factory=list, max_length=20)
    must_haves: list[str] = Field(default_factory=list, max_length=20)
    looking_for: str | None = Field(default=None, max_length=2000)


class QuestionConfig(BaseModel):
    """Screening question config item."""

    text: str = Field(..., min_length=1, max_length=1000)
    required: bool = True


class CalendarConfig(BaseModel):
    """cal.com config section."""

    calcom_api_key: str
    calcom_event_type_id: str


class AvatarConfig(BaseModel):
    """Tavus config section."""

    tavus_api_key: str


class HeartConfig(BaseModel):
    """Top-level static Heart config."""

    profile: ProfileConfig
    persona: PersonaConfig
    expectations: ExpectationsConfig
    screening_questions: list[QuestionConfig] = Field(..., min_length=1, max_length=15)
    shareable_slug: str = Field(..., pattern=r"^[a-z0-9\-]+$", max_length=50)
    calendar: CalendarConfig
    avatar: AvatarConfig


class HeartConfigLoader:
    """Loads and persists static Heart configuration."""

    def __init__(self, config_path: str = "config/heart_config.yaml"):
        self.config_path = config_path
        self.config: HeartConfig | None = None

    def _resolve_env_vars(self, value: str) -> str:
        """Replace ${ENV_VAR} tokens with values from os.environ."""

        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            env_val = os.environ.get(var_name)
            if env_val is None:
                raise ValueError(
                    f"Environment variable '{var_name}' not set (referenced in heart_config.yaml)"
                )
            return env_val

        return re.sub(r"\$\{(\w+)\}", replacer, value)

    def _resolve_env_recursive(self, data):
        """Recursively resolve env vars in nested YAML payloads."""
        if isinstance(data, str):
            return self._resolve_env_vars(data)
        if isinstance(data, dict):
            return {k: self._resolve_env_recursive(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._resolve_env_recursive(item) for item in data]
        return data

    def load(self) -> HeartConfig:
        """Load, resolve env vars, and validate static Heart YAML config."""
        path = Path(self.config_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path

        if not path.exists():
            raise FileNotFoundError(f"Heart config not found at {path}")

        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        resolved = self._resolve_env_recursive(raw)
        self.config = HeartConfig(**resolved)
        return self.config

    async def seed_database(self, db_session: AsyncSession) -> HeartDb:
        """Upsert the Heart row and fully sync screening questions from config."""
        if not self.config:
            raise RuntimeError("Config not loaded. Call load() first.")

        cfg = self.config
        result = await db_session.execute(
            select(HeartDb).where(HeartDb.shareable_slug == cfg.shareable_slug)
        )
        heart = result.scalars().first()

        if heart:
            heart.display_name = cfg.profile.display_name
            heart.bio = cfg.profile.bio
            heart.photo_url = cfg.profile.photo_url
            heart.video_url = cfg.profile.video_url
            heart.persona = cfg.persona.model_dump()
            heart.expectations = cfg.expectations.model_dump()
            heart.shareable_slug = cfg.shareable_slug
            heart.calcom_event_type_id = cfg.calendar.calcom_event_type_id
            heart.is_active = True
            db_session.add(heart)
        else:
            heart = HeartDb(
                clerk_user_id=None,
                email=None,
                display_name=cfg.profile.display_name,
                bio=cfg.profile.bio,
                photo_url=cfg.profile.photo_url,
                video_url=cfg.profile.video_url,
                persona=cfg.persona.model_dump(),
                expectations=cfg.expectations.model_dump(),
                shareable_slug=cfg.shareable_slug,
                calcom_event_type_id=cfg.calendar.calcom_event_type_id,
                is_active=True,
            )
            db_session.add(heart)

        await db_session.flush()

        await db_session.execute(
            delete(ScreeningQuestionDb).where(ScreeningQuestionDb.heart_id == heart.id)
        )

        for index, question in enumerate(cfg.screening_questions):
            db_session.add(
                ScreeningQuestionDb(
                    heart_id=heart.id,
                    question_text=question.text,
                    order_index=index,
                    is_required=question.required,
                )
            )

        await db_session.commit()
        await db_session.refresh(heart)
        return heart
