from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from backend.core.config import settings
from backend.database.redis import redis_breaker
import logging

logger = logging.getLogger(__name__)

MEMORY_STORAGE_URI = "memory://"

def _rate_limit_key_func(request: Request):
    """
    Key function for rate limiting.

    Always returns a stable key (client IP) so that fallback storage backends,
    such as in-memory storage, can still enforce limits even when Redis is
    unavailable.
    """
    if not redis_breaker.is_available():
        # Redis is unavailable; rely on fallback storage (e.g., in-memory) but
        # still use a proper key so rate limiting remains effective.
        logger.warning("Redis unavailable for rate limiting; using fallback storage with client IP key.")
    return get_remote_address(request)

limiter = Limiter(
    key_func=_rate_limit_key_func,
    storage_uri=settings.redis_url.replace("localhost", "127.0.0.1") if settings.redis_url else MEMORY_STORAGE_URI,
    enabled=True,
    headers_enabled=True,
    swallow_errors=True
)

def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limit_exceeded", "message": "Too many requests."}
    )

