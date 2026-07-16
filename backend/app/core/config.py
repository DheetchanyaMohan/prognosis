"""Application configuration.

Settings are loaded from environment variables (and a local .env file in
development) via pydantic-settings. Import get_settings() rather than
instantiating Settings() directly so the values are cached and consistent
across the app.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Central application settings.

    Every field has a safe development default so the app can start with
    no .env file present; production deployments override via real
    environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    app_name: str = "ML Experiment Diagnosis & Decision Support System"
    environment: str = "development"
    debug: bool = False

    # API
    api_v1_prefix: str = "/api/v1"
    cors_allow_origins: list[str] = ["http://localhost:5173"]

    # Database
    database_url: str = f"sqlite:///{BACKEND_ROOT / 'data' / 'db' / 'experiments.db'}"

    # External services (used by later phases, not the current scaffold)
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-5"

    # LLM service layer (app.llm) — provider-independent configuration
    llm_provider: str = "anthropic"
    llm_max_retries: int = 3
    llm_retry_backoff_seconds: float = 1.0

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    lru_cache ensures the environment is only parsed once per process,
    and lets tests override settings via dependency injection if needed.
    """
    return Settings()