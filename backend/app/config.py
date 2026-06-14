from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server-side defaults. Per-user credentials normally arrive via request
    headers (see app.deps.Credentials); these are fallbacks only."""

    angel_client_id: str = ""
    angel_api_key: str = ""
    angel_pin: str = ""
    angel_totp_secret: str = ""
    groq_api_key: str = ""

    groq_model: str = "llama3-70b-8192"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
