import logging
import os
from enum import Enum
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv
from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(override=False)


logger = logging.getLogger(__name__)


class EnvironmentOption(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class LLMProvider(str, Enum):
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"


class TTSProvider(str, Enum):
    DEEPGRAM = "deepgram"
    SMALLESTAI = "smallestai"


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    ENV: EnvironmentOption = EnvironmentOption.PROD
    APP_ENV: Optional[str] = None
    API: str = "/api"
    API_V1_STR: str = "/api/v1"
    API_STR: str = "/api"
    MCP_STR: str = "/mcp"
    MCP_SERVER_URL: str = "http://127.0.0.1:8000/mcp"
    PROJECT_NAME: str = "Valentine Hotline"
    DEBUG: Optional[bool] = None
    FRONTEND_URL: str = "http://localhost:5173"

    # CORS
    CORS_ORIGINS: Optional[str] = None
    CORS_ORIGINS_STR: Optional[str] = ""
    BACKEND_CORS_ORIGINS: Optional[list[str]] = None

    # Database
    DATABASE_URL: Optional[str] = None
    DB_USER: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_PASSWORD: SecretStr
    DB_SSL: Optional[str] = None
    DB_FORCE_ROLL_BACK: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    ADMIN_API_KEY: Optional[str] = None
    DASHBOARD_API_KEY: Optional[str] = None
    MAX_SESSIONS_PER_DAY: int = 3
    MAX_CONCURRENT_SESSIONS: int = 5
    SESSION_PENDING_TIMEOUT: int = 300
    SESSION_MAX_DURATION: int = 1800
    VERDICT_THRESHOLD: float = 65.0
    DATA_RETENTION_DAYS: int = 90
    MAX_REQUEST_BODY_BYTES: int = 1_048_576
    ALLOWED_HOSTS: Optional[str] = None
    BACKEND_ALLOWED_HOSTS: Optional[list[str]] = None
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None

    @model_validator(mode="after")
    def set_debug_default(self):
        if self.DEBUG is None:
            self.DEBUG = self.ENV == EnvironmentOption.DEV

        raw_origins = self.CORS_ORIGINS or self.CORS_ORIGINS_STR or ""
        if raw_origins:
            cleaned = raw_origins.strip()
            if cleaned.startswith("[") and cleaned.endswith("]"):
                import json

                parsed = json.loads(cleaned)
                if isinstance(parsed, list):
                    self.BACKEND_CORS_ORIGINS = [
                        str(origin).strip() for origin in parsed if str(origin).strip()
                    ]
                else:
                    self.BACKEND_CORS_ORIGINS = ["*"]
            else:
                self.BACKEND_CORS_ORIGINS = [
                    origin.strip()
                    for origin in raw_origins.split(",")
                    if origin.strip()
                ]
        else:
            self.BACKEND_CORS_ORIGINS = ["*"]

        raw_hosts = self.ALLOWED_HOSTS or ""
        if raw_hosts:
            self.BACKEND_ALLOWED_HOSTS = [
                host.strip() for host in raw_hosts.split(",") if host.strip()
            ]
        else:
            self.BACKEND_ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
        return self

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        from urllib.parse import quote_plus

        if self.DATABASE_URL:
            return self.DATABASE_URL

        db_password = quote_plus(self.DB_PASSWORD.get_secret_value())
        return (
            f"postgresql+asyncpg://{quote_plus(self.DB_USER)}:{db_password}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def SQLALCHEMY_CONNECT_ARGS(self) -> dict[str, object]:
        args: dict[str, object] = {"statement_cache_size": 0}

        if self.DB_SSL:
            ssl_mode = self.DB_SSL.strip().lower()
            if ssl_mode in {"disable", "false", "0", "no"}:
                args["ssl"] = False
            else:
                args["ssl"] = True

        return args

    # LLM Configs
    LLM_PROVIDER: LLMProvider = LLMProvider.OPENAI
    MODEL_NAME: Optional[str] = None

    OPENAI_API_KEY: Optional[SecretStr] = None
    HUGGINGFACE_API_TOKEN: Optional[SecretStr] = None
    TTS: TTSProvider = TTSProvider.DEEPGRAM
    DEEPGRAM_TTS_MODEL: str = "aura-2-andromeda-en"
    SMALLEST_TTS_MODEL: str = "lightning-v2"

    # Clerk Authentication (Suitor auth)
    CLERK_JWKS_URL: str
    CLERK_SECRET_KEY: SecretStr
    CLERK_WEBHOOK_SECRET: SecretStr
    CLERK_ISSUER: Optional[str] = None
    CLERK_AUDIENCE: Optional[str] = None
    CLERK_AUTHORIZED_PARTIES: Optional[str] = None
    CLERK_PUBLISHABLE_KEY: Optional[str] = None

    # Milestone placeholders for future integrations
    LIVEKIT_API_KEY: Optional[SecretStr] = None
    LIVEKIT_API_SECRET: Optional[SecretStr] = None
    LIVEKIT_URL: Optional[str] = None
    TAVUS_API_KEY: Optional[SecretStr] = None
    SMALLEST_AI_API_KEY: Optional[SecretStr] = None
    SMALLEST_LLM_BASE_URL: str = "https://llm-api.smallest.ai/v1"
    SMALLEST_LLM_MODEL: str = "electron-v2"
    DEEPGRAM_API_KEY: Optional[SecretStr] = None
    ANTHROPIC_API_KEY: Optional[SecretStr] = None
    CALCOM_API_KEY: Optional[SecretStr] = None
    CALCOM_EVENT_TYPE_ID: Optional[str] = None

    @property
    def CLERK_WEBHOOK_SECRET_VALUE(self) -> Optional[str]:
        return self.CLERK_WEBHOOK_SECRET.get_secret_value()

    @property
    def CLERK_AUDIENCES(self) -> list[str]:
        if not self.CLERK_AUDIENCE:
            return []
        return [aud.strip() for aud in self.CLERK_AUDIENCE.split(",") if aud.strip()]

    @property
    def CLERK_AUTHORIZED_PARTY_LIST(self) -> list[str]:
        if not self.CLERK_AUTHORIZED_PARTIES:
            return []
        return [
            party.strip()
            for party in self.CLERK_AUTHORIZED_PARTIES.split(",")
            if party.strip()
        ]

    PAGE: int = 1
    PAGE_SIZE: int = 10
    ORDERING: str = "-id"


@lru_cache()
def get_config() -> Config:
    cfg = Config()
    if cfg.SMALLEST_AI_API_KEY and not os.environ.get("SMALLEST_API_KEY"):
        os.environ["SMALLEST_API_KEY"] = cfg.SMALLEST_AI_API_KEY.get_secret_value()
    return cfg


config = get_config()
