from functools import lru_cache
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: Literal["development", "test", "staging", "production"] = "development"
    database_url: str = "sqlite:///./farmwise.db"
    jwt_secret: str = "dev-only-change-me"
    google_client_id: str = "263684588844-r1cllo3a62gfisbstsqevnmgnvu1j3pd.apps.googleusercontent.com"
    google_translate_api_key: str = ""
    redis_url: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,https://tharun-rk.github.io"
    demo_data: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @model_validator(mode="after")
    def require_strong_production_jwt_secret(self) -> "Settings":
        if self.app_env == "production":
            secret_bytes = self.jwt_secret.encode("utf-8")
            if self.jwt_secret == "dev-only-change-me" or len(secret_bytes) < 32:
                raise ValueError(
                    "JWT_SECRET must be configured with at least 32 bytes when APP_ENV=production"
                )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
