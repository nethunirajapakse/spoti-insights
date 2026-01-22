"""
Redis connection and utility module for token caching and distributed locking.
"""
import redis.asyncio as redis
from backend.core.config import settings
import logging
import re

logger = logging.getLogger(__name__)

# --- Lazy Initialization State ---
# These variables hold the pool state so we don't connect until actually needed
_pool = None
_pool_initialization_error = None

def _get_pool():
    """
    Internal helper to initialize the connection pool only when needed.
    Caches the pool and any initialization errors to satisfy lazy-loading requirements.
    """
    global _pool, _pool_initialization_error

    # If an earlier attempt failed, re-raise the same error (caching the failure)
    if _pool_initialization_error:
        raise _pool_initialization_error

    if _pool is None:
        # 1. Check if the URL is even configured
        if not settings.redis_url:
            _pool_initialization_error = RuntimeError(
                "Redis is not configured. Please set REDIS_URL environment variable."
            )
            raise _pool_initialization_error
        
        try:
            # 2. Initialize the pool using settings from core/config.py
            _pool = redis.ConnectionPool.from_url(
                settings.redis_url, 
                decode_responses=True,
                max_connections=settings.redis_max_connections,
                socket_connect_timeout=settings.redis_socket_connect_timeout,
                socket_keepalive=True,
                health_check_interval=settings.redis_health_check_interval
            )
            logger.info("Redis connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis pool: {e}")
            _pool_initialization_error = e
            raise e
            
    return _pool

# --- FastAPI Dependencies & Health Checks ---

async def get_redis():
    """
    FastAPI dependency for Redis connections.
    Yields a Redis client and ensures proper cleanup.
    """
    try:
        pool = _get_pool()
        client = redis.Redis(connection_pool=pool)
        try:
            yield client
        finally:
            # Cleanly close the specific client connection
            await client.aclose()
    except Exception as e:
        logger.error(f"Redis dependency error: {e}")
        raise

async def ping_redis() -> bool:
    """
    Health check function to verify Redis connectivity.
    Returns False instead of raising an exception if Redis is unavailable.
    """
    try:
        pool = _get_pool()
        client = redis.Redis(connection_pool=pool)
        try:
            await client.ping()
            return True
        finally:
            await client.aclose()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False

# --- Token Cache Implementation ---

class RedisTokenCache:
    """
    Redis-backed token cache with distributed locking support.
    Provides methods for token storage, retrieval, and invalidation.
    """
    
    TOKEN_PREFIX = "spotify:token:"
    LOCK_PREFIX = "spotify:lock:refresh:"
    DEFAULT_LOCK_TIMEOUT = 10  # seconds
    TOKEN_BUFFER = 60  # Safety buffer for expiry
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def _sanitize_user_id(self, user_id: str) -> str:
        """Only allows alphanumeric characters, hyphens, and underscores."""
        if not user_id:
            raise ValueError("user_id cannot be empty")
        if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
            raise ValueError(f"invalid characters in user_id: {user_id}")
        return user_id
    
    def _get_token_key(self, user_id: str) -> str:
        return f"{self.TOKEN_PREFIX}{self._sanitize_user_id(user_id)}"
    
    def _get_lock_key(self, user_id: str) -> str:
        return f"{self.LOCK_PREFIX}{self._sanitize_user_id(user_id)}"
    
    async def get_token(self, user_id: str) -> str | None:
        try:
            token = await self.redis.get(self._get_token_key(user_id))
            if token:
                logger.debug(f"Cache hit for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Error retrieving token: {e}")
            return None
    
    async def set_token(self, user_id: str, access_token: str, expires_in: int) -> bool:
        try:
            # TTL: expires_in minus our safety buffer
            ttl = max(1, expires_in - self.TOKEN_BUFFER)
            await self.redis.set(self._get_token_key(user_id), access_token, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Error storing token: {e}")
            return False
    
    async def invalidate_token(self, user_id: str) -> bool:
        try:
            return bool(await self.redis.delete(self._get_token_key(user_id)))
        except Exception as e:
            logger.error(f"Error invalidating token: {e}")
            return False
    
    def get_refresh_lock(self, user_id: str, timeout: int | None = None):
        lock_timeout = timeout or self.DEFAULT_LOCK_TIMEOUT
        return self.redis.lock(
            self._get_lock_key(user_id),
            timeout=lock_timeout,
            blocking=True,
            blocking_timeout=lock_timeout
        )
    
    async def clear_all_tokens(self) -> int:
        """Deletes all keys matching the token prefix."""
        try:
            count = 0
            async for key in self.redis.scan_iter(f"{self.TOKEN_PREFIX}*"):
                count += await self.redis.delete(key)
            logger.info(f"Cleared {count} tokens from cache")
            return count
        except Exception as e:
            logger.error(f"Error clearing tokens: {e}")
            return 0
    
    async def get_cache_stats(self) -> dict:
        """Retrieve count of cached tokens and Redis memory usage."""
        try:
            token_count = 0
            async for _ in self.redis.scan_iter(f"{self.TOKEN_PREFIX}*"):
                token_count += 1
            
            info = await self.redis.info("memory")
            return {
                "cached_tokens": token_count,
                "redis_memory_used": info.get("used_memory_human", "N/A"),
                "redis_memory_peak": info.get("used_memory_peak_human", "N/A")
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}

def get_redis_token_cache(redis_client: redis.Redis) -> RedisTokenCache:
    """Dependency factory for RedisTokenCache."""
    return RedisTokenCache(redis_client)