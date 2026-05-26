"""
Health check endpoints for monitoring application and Redis status.
"""
from typing import Annotated
import logging

from fastapi import APIRouter, Depends, HTTPException, status
import redis.asyncio as redis
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.database.redis import get_redis, RedisTokenCache
from backend.database.connection import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])

DbSession = Annotated[Session, Depends(get_db)]
RedisClient = Annotated[redis.Redis | None, Depends(get_redis)]


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "spotify-analytics-api"
    }


@router.get("/redis")
async def redis_health_check(redis_client: RedisClient):
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
        logger.exception("Redis health check failed")
        return {
            "status": "degraded",
            "redis": "unavailable",
            "detail": "Ping Failed"
        }


@router.get("/redis/stats")
async def redis_stats(redis_client: RedisClient):
    """Detailed Redis stats including token count. Slower due to full key scan."""
    if not redis_client:
        return {"status": "degraded", "redis": "unavailable"}
    try:
        cache = RedisTokenCache(redis_client)
        stats = await cache.get_cache_stats(include_token_count=True)
        return {"status": "healthy", "redis": "connected", "stats": stats}
    except Exception:
        logger.exception("Redis stats check failed")
        return {"status": "degraded", "redis": "unavailable"}


@router.get("/full")
async def full_health_check(
    db: DbSession,
    redis_client: RedisClient,
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
async def database_health_check(db: DbSession):
    """Check database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.exception("Database health check failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {str(e)}"
        )
