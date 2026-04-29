"""
Health check endpoints for monitoring application and Redis status.
"""
from fastapi import APIRouter, Depends, HTTPException, status
import redis.asyncio as redis
from backend.database.redis import get_redis, RedisTokenCache
from backend.database.connection import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "spotify-analytics-api"
    }


@router.get("/redis")
async def redis_health_check(redis_client: redis.Redis | None = Depends(get_redis)):
    if not redis_client:
        return {
            "status": "degraded",
            "redis": "unavailable",
            "detail": "Connection Failed"
        }
    try:
        await redis_client.ping()
        cache = RedisTokenCache(redis_client)
        # include_token_count=False (default): fast O(1) memory stats only.
        # Avoids a full key scan on every health check as the cache grows.
        stats = await cache.get_cache_stats()
        return {"status": "healthy", "redis": "connected", "stats": stats}
    except Exception:
        logger.error("Redis health check failed", exc_info=True)
        return {
            "status": "degraded",
            "redis": "unavailable",
            "detail": "Ping Failed"
        }


@router.get("/redis/stats")
async def redis_stats(redis_client: redis.Redis | None = Depends(get_redis)):
    """Detailed Redis stats including token count. Slower due to full key scan."""
    if not redis_client:
        return {"status": "degraded", "redis": "unavailable"}
    try:
        cache = RedisTokenCache(redis_client)
        stats = await cache.get_cache_stats(include_token_count=True)
        return {"status": "healthy", "redis": "connected", "stats": stats}
    except Exception:
        logger.error("Redis stats check failed", exc_info=True)
        return {"status": "degraded", "redis": "unavailable"}


@router.get("/full")
async def full_health_check(
    db: Session = Depends(get_db),
    redis_client: redis.Redis | None = Depends(get_redis)
):
    health_status = {"status": "healthy", "checks": {}}

    # DB Check
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "connected"
    except Exception:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = "error"

    # Redis Check
    try:
        if redis_client:
            await redis_client.ping()
            health_status["checks"]["redis"] = "connected"
        else:
            health_status["status"] = "degraded"
            health_status["checks"]["redis"] = "unavailable"
    except Exception:
        health_status["status"] = "degraded"
        health_status["checks"]["redis"] = "unavailable"

    # Return 200 even if degraded so monitoring knows the API is ALIVE but limited
    return health_status


@router.get("/database")
async def database_health_check(db: Session = Depends(get_db)):
    """Check database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {str(e)}"
        )
