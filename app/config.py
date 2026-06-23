from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LOGLENS_",
        extra="ignore",
    )

    app_name: str = "LogLens"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    database_url: str = "sqlite:///loglens.db"
    max_upload_bytes: int = 5 * 1024 * 1024
    alert_webhook_url: str | None = None
    alert_webhook_timeout_seconds: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
