from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    # Env vars use the APP_ prefix, e.g. APP_LOG_LEVEL, APP_DATABASE_URL.
    model_config = SettingsConfigDict(env_prefix="APP_")

    log_level: str = "INFO"
    debug: bool = False
    allowed_origins: str = "*"
    # Async SQLAlchemy URL. Defaults to the docker-compose `db` service.
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/casestudy"
