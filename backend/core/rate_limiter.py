from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

from backend.core.config import settings

logger = logging.getLogger(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url or "memory://",
    default_limits=["200/hour"]
)

async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    logger.warning(f"Rate limit exceeded for IP: {get_remote_address(request)}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "detail": str(exc.detail) if hasattr(exc, 'detail') else "Rate limit exceeded"
        }
    )
