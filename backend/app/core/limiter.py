"""Shared SlowAPI limiter for sensitive authentication and media endpoints."""
import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

log = logging.getLogger("farmwise.rate_limit")
if settings.app_env == "production" and not settings.redis_url:
    log.warning("rate_limit_storage=process_memory; configure REDIS_URL to share limits across instances")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri=settings.redis_url or "memory://",
)
