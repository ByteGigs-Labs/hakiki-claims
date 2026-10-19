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
    max_body_bytes: int = 64 * 1024
    max_upload_bytes: int = 2 * 1024 * 1024
    max_batch_rows: int = 500
    login_ip_per_minute: int = 20
    login_account_per_five_minutes: int = 5
    check_per_minute: int = 60
    batch_per_hour: int = 10
    llm_api_key: SecretStr | None = None
    llm_model: str = "claude-haiku-5-5"

    @field_validator("cors_origins")
    @classmethod
    def reject_wildcard(cls, origins: list[str]) -> list[str]:
        if "*" in origins:
            raise ValueError("CORS origins must be explicit when credentials are allowed")
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
