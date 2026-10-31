import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_development_allows_local_placeholder_secret():
    settings = Settings(_env_file=None, app_env="development")

    assert settings.jwt_secret == "dev-only-change-me"


@pytest.mark.parametrize("secret", ["dev-only-change-me", "too-short"])
def test_production_rejects_missing_or_weak_jwt_secret(secret: str):
    with pytest.raises(ValidationError, match="JWT_SECRET must be configured"):
        Settings(_env_file=None, app_env="production", jwt_secret=secret)


def test_production_accepts_secret_with_at_least_32_bytes():
    settings = Settings(
        _env_file=None,
        app_env="production",
        jwt_secret="a" * 32,
    )

    assert settings.app_env == "production"
