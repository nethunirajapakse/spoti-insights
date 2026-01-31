"""
Health check endpoints for monitoring application and Redis status.
"""
from fastapi import APIRouter, Depends, HTTPException, status
import redis
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
async def redis_health_check(redis_client: redis.Redis  = Depends(get_redis)):
    """
    Check Redis connectivity and get cache statistics.
    """
    try:
        # Test Redis connection
        await redis_client.ping()
        
        # Get cache statistics
        cache = RedisTokenCache(redis_client)
        stats = await cache.get_cache_stats()
        
        return {
            "status": "healthy",
            "redis": "connected",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis unavailable: {str(e)}"
        )

@router.get("/database")
async def database_health_check(db: Session = Depends(get_db)):
    """
    Check database connectivity.
    """
    try:
        # Test database connection
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

@router.get("/full")
async def full_health_check(
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    Comprehensive health check for all services.
    """
    health_status = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "connected"
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = f"error: {str(e)}"
    
    # Check Redis
    try:
        await redis_client.ping()
        cache = RedisTokenCache(redis_client)
        stats = await cache.get_cache_stats()
        health_status["checks"]["redis"] = {
            "status": "connected",
            "cached_tokens": stats.get("cached_tokens", 0)
        }
    except Exception as e:
        logger.error(f"Redis check failed: {e}")
        health_status["status"] = "degraded"
        health_status["checks"]["redis"] = f"error: {str(e)}"
    
    if health_status["status"] != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return health_status
