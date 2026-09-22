from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "enterprise-document-intelligence"
    app_env: str = "local"
    log_level: str = "INFO"

    execution_mode: str = "local"

    database_backend: str = "postgres"
    database_host: str
    database_port: int = 5432
    database_name: str
    database_user: str
    database_password: str

    storage_backend: str = "local"
    queue_backend: str = "local"
    notification_backend: str = "local"
    vector_backend: str = "local"
    model_backend: str = "ollama"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()