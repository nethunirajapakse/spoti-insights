from slowapi import Limiter
from slowapi.util import get_remote_address
from backend.core.config import settings
import logging

logger = logging.getLogger(__name__)

def _get_redis_url() -> str:
    """Get Redis URL from settings for rate limiting."""
    return settings.redis_url

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
        swallow_errors=True  # Don't break app if Redis is down
    )
    logger.info("SlowAPI initialized with Redis backend")
except Exception as e:
    logger.warning(f"Failed to initialize SlowAPI with Redis, falling back to in-memory: {e}")
    # Fallback to in-memory limiter if Redis is unavailable
    limiter = Limiter(
        key_func=_rate_limit_key_func,
        enabled=True,
        headers_enabled=True
    )

# Export limiter instance
__all__ = ["limiter"]
