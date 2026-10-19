from functools import lru_cache

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str = "redis://127.0.0.1:6379/0"
    hmac_key: SecretStr
    cors_origins: list[str] = ["http://localhost:5173"]
    cookie_name: str = "hakiki_session"
    cookie_secure: bool = True
    session_ttl_hours: int = 12

    @field_validator("cors_origins")
    @classmethod
    def reject_wildcard(cls, origins: list[str]) -> list[str]:
        if "*" in origins:
            raise ValueError("CORS origins must be explicit when credentials are allowed")
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
