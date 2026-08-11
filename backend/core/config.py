"""
Centralized application configuration.

All environment variables are read here via pydantic-settings and exposed as a
single typed `settings` object. Application code must import `settings` from
this module instead of calling `os.getenv()` directly.
"""

from __future__ import annotations

import secrets
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    APP_ENV: str = "development"  # development | test | production
    APP_NAME: str = "Cozy AI Productivity & RAG Intelligence System"
    APP_VERSION: str = "2.1.0"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./cozy_productivity.db"

    # --- Auth ---
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    SEED_DEMO: bool = False

    # --- CORS ---
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"]
    )

    # --- RAG ---
    RAG_PROVIDER: str = "ollama"
    RAG_MODEL: str = ""
    CHROMA_PATH: str = "./chroma_db"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    RAG_TOP_K: int = 8
    RAG_RERANK_LIMIT: int = 5
    RAG_RELEVANCE_THRESHOLD: float = 0.25
    RAG_MAX_CONTEXT_CHARS: int = 4000
    RAG_MAX_SOURCES: int = 5

    # --- LLM providers ---
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    LLM_TIMEOUT_SECONDS: float = 10.0
    LLM_MAX_RETRIES: int = 1
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GROK_API_KEY: str = ""
    GROK_MODEL: str = "grok-beta"

    # --- Rate limiting (in-process sliding window) ---
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_PER_MINUTE: int = 20
    RATE_LIMIT_RAG_PER_MINUTE: int = 30
    RATE_LIMIT_GENERAL_PER_MINUTE: int = 120

    # --- Security / observability ---
    LOG_FORMAT: str = "text"  # text | json
    TOKEN_BLACKLIST_TTL_DAYS: int = 8  # >= ACCESS_TOKEN_EXPIRE_MINUTES

    # --- RAG answer cache (in-process, per user) ---
    RAG_CACHE_ENABLED: bool = True
    RAG_CACHE_TTL_SECONDS: int = 300
    RAG_CACHE_MAX_ENTRIES: int = 128

    # --- Model allowlist per provider (empty list = any model allowed) ---
    ALLOWED_MODELS: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "ollama": [],  # local; user-controlled
            "openai": ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o"],
            "gemini": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"],
            "grok": ["grok-beta", "grok-2-latest"],
        }
    )

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def _validate_jwt_secret(cls, v: str, info) -> str:
        """Fail fast in production when the JWT secret is missing."""
        env = info.data.get("APP_ENV", "development")
        if env == "production" and not v:
            raise ValueError(
                "JWT_SECRET_KEY is required in production. "
                "Set it via environment variable or .env file."
            )
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def is_testing(self) -> bool:
        return self.APP_ENV.lower() == "test"

    def resolved_jwt_secret(self) -> str:
        """Return the effective JWT secret.

        In development, generate a single random ephemeral secret on first use
        so the app works out of the box without a committed default while
        remaining stable for the lifetime of the process. In production the
        secret must already be set (see validator).
        """
        if self.JWT_SECRET_KEY:
            return self.JWT_SECRET_KEY
        if self.is_production:
            raise ValueError("JWT_SECRET_KEY is required in production.")
        if self._resolved_secret is None:
            self._resolved_secret = secrets.token_urlsafe(48)
        return self._resolved_secret

    _resolved_secret: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
