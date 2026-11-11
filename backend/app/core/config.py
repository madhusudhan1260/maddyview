"""Environment-based configuration. All settings come from FINPILOT_* env vars or backend/.env."""

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FINPILOT_", env_file=".env", extra="ignore")

    env: str = "development"
    app_name: str = "MaddyView"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+psycopg://localhost:5432/finpilot"
    test_database_url: str = "postgresql+psycopg://localhost:5432/finpilot_test"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5190", "http://127.0.0.1:5190"]
    session_ttl_hours: int = 12
    session_cookie_name: str = "finpilot_session"
    cookie_secure: bool = False
    auth_rate_limit_per_minute: int = 10
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
