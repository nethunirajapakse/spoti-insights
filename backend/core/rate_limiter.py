from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from backend.core.config import settings
import logging
import redis

logger = logging.getLogger(__name__)

MEMORY_STORAGE_URI = "memory://"

def _get_redis_url() -> str:
    """Get Redis URL from settings for rate limiting."""
    redis_url = getattr(settings, "redis_url", None)
    if not redis_url:
        return MEMORY_STORAGE_URI
    
    try:
        url = redis_url.replace("localhost", "127.0.0.1")
        test_client = redis.from_url(url, socket_connect_timeout=1)
        test_client.ping()
        return url
    except (redis.ConnectionError, redis.TimeoutError) as e:
        logger.warning(f"Redis connection failed ({e}). Falling back to 'memory://'")
        return MEMORY_STORAGE_URI

def _rate_limit_key_func(request):
    """
    Generate rate limit key based on user identity.
    Falls back to IP address if user is not authenticated.
    """
    # Try to get user from request state (set by auth middleware)
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "spotify_id"):
        return f"user:{user.spotify_id}"
    
    # Fall back to IP-based rate limiting
    return get_remote_address(request)

# Initialize limiter with Redis backend
try:
    limiter = Limiter(
        key_func=_rate_limit_key_func,
        storage_uri=_get_redis_url(),
        enabled=True,
        headers_enabled=True,
        swallow_errors=True
    )
    logger.info("SlowAPI initialized with Redis backend")
except Exception as e:
    logger.warning(f"Failed to initialize SlowAPI with Redis, falling back to in-memory: {e}")
    # Fallback to in-memory limiter if Redis is unavailable
    limiter = Limiter(
        key_func=_rate_limit_key_func,
        storage_uri=MEMORY_STORAGE_URI,
        enabled=True,
        headers_enabled=True
    )

def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors with user-friendly messages."""
    logger.warning(f"Rate limit exceeded for: {_rate_limit_key_func(request)}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail) if hasattr(exc, 'detail') else "Rate limit exceeded"
        }
    )

# Export limiter instance and handler
__all__ = ["limiter", "rate_limit_handler"]
