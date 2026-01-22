"""
Redis connection and utility module for token caching and distributed locking.
"""
import redis.asyncio as redis
from backend.core.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Global connection pool - initialized lazily
_pool: Optional[redis.ConnectionPool] = None
_pool_initialization_error: Optional[Exception] = None


def _get_pool() -> redis.ConnectionPool:
    """
    Get or create the Redis connection pool lazily.
    
    This allows the application to start even if Redis is not configured,
    and provides clear error messages when Redis operations are attempted
    without proper configuration.
    
    Returns:
        Redis connection pool instance
        
    Raises:
        RuntimeError: If Redis URL is not configured
        Exception: If pool creation fails for other reasons
    """
    global _pool, _pool_initialization_error
    
    # Return existing pool if already initialized
    if _pool is not None:
        return _pool
    
    # If previous initialization failed, raise the same error
    if _pool_initialization_error is not None:
        raise _pool_initialization_error
    
    # Check if Redis URL is configured
    if settings.redis_url is None:
        error = RuntimeError(
            "Redis is not configured. Please set the REDIS_URL environment variable. "
            "Example: REDIS_URL=redis://localhost:6379/0"
        )
        _pool_initialization_error = error
        logger.error(str(error))
        raise error
    
    # Try to create the connection pool
    try:
        _pool = redis.ConnectionPool.from_url(
            settings.redis_url, 
            decode_responses=True,
            max_connections=settings.redis_max_connections,
            socket_connect_timeout=settings.redis_socket_connect_timeout,
            socket_keepalive=True,
            health_check_interval=settings.redis_health_check_interval
        )
        # Mask sensitive parts of URL for logging
        safe_url = settings.redis_url.split('@')[-1] if '@' in settings.redis_url else settings.redis_url
        logger.info(
            f"Redis connection pool initialized successfully "
            f"(url=...{safe_url}, max_connections={settings.redis_max_connections})"
        )
        return _pool
    except Exception as e:
        error = RuntimeError(f"Failed to create Redis connection pool: {str(e)}")
        _pool_initialization_error = error
        logger.error(str(error))
        raise error

async def get_redis():
    """
    FastAPI dependency for Redis connections.
    Yields a Redis client and ensures proper cleanup.
    
    Raises:
        RuntimeError: If Redis is not configured or pool initialization fails
    """
    pool = _get_pool()  # Lazy initialization
    client = redis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.aclose()

async def ping_redis() -> bool:
    """
    Health check function to verify Redis connectivity.
    Returns True if Redis is accessible, False otherwise.
    
    Note: Returns False if Redis is not configured or if connection fails.
    """
    try:
        pool = _get_pool()  # Lazy initialization
        client = redis.Redis(connection_pool=pool)
        try:
            await client.ping()
            logger.info("Redis connection successful")
            return True
        finally:
            await client.aclose()
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return False

class RedisTokenCache:
    """
    Redis-backed token cache with distributed locking support.
    Provides methods for token storage, retrieval, and invalidation.
    """
    
    TOKEN_PREFIX = "spotify:token:"
    LOCK_PREFIX = "spotify:lock:refresh:"
    DEFAULT_LOCK_TIMEOUT = 10  # seconds
    TOKEN_BUFFER = 60  # subtract 60 seconds from TTL for safety
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def _get_token_key(self, user_id: str) -> str:
        """Generate Redis key for storing token."""
        return f"{self.TOKEN_PREFIX}{user_id}"
    
    def _get_lock_key(self, user_id: str) -> str:
        """Generate Redis key for refresh lock."""
        return f"{self.LOCK_PREFIX}{user_id}"
    
    async def get_token(self, user_id: str) -> str | None:
        """
        Retrieve access token from cache.
        
        Args:
            user_id: Spotify user ID
            
        Returns:
            Access token if exists and not expired, None otherwise
        """
        token_key = self._get_token_key(user_id)
        try:
            token = await self.redis.get(token_key)
            if token:
                logger.debug(f"Token cache hit for user {user_id}")
            return token
        except Exception as e:
            logger.error(f"Error retrieving token from Redis: {e}")
            return None
    
    async def set_token(self, user_id: str, access_token: str, expires_in: int) -> bool:
        """
        Store access token in cache with TTL.
        
        Args:
            user_id: Spotify user ID
            access_token: Spotify access token
            expires_in: Token lifetime in seconds
            
        Returns:
            True if successful, False otherwise
        """
        token_key = self._get_token_key(user_id)
        try:
            # Apply safety buffer to prevent using expired tokens
            ttl = max(1, expires_in - self.TOKEN_BUFFER)
            await self.redis.set(token_key, access_token, ex=ttl)
            logger.info(f"Cached token for user {user_id} with TTL {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Error storing token in Redis: {e}")
            return False
    
    async def invalidate_token(self, user_id: str) -> bool:
        """
        Remove token from cache (used on logout).
        
        Args:
            user_id: Spotify user ID
            
        Returns:
            True if key was deleted, False otherwise
        """
        token_key = self._get_token_key(user_id)
        try:
            deleted = await self.redis.delete(token_key)
            if deleted:
                logger.info(f"Invalidated token for user {user_id}")
            return bool(deleted)
        except Exception as e:
            logger.error(f"Error invalidating token in Redis: {e}")
            return False
    
    def get_refresh_lock(self, user_id: str, timeout: int | None = None):
        """
        Create a distributed lock for token refresh operations.
        
        Args:
            user_id: Spotify user ID
            timeout: Lock timeout in seconds (default: DEFAULT_LOCK_TIMEOUT)
            
        Returns:
            Redis Lock instance that can be used as async context manager
        """
        lock_key = self._get_lock_key(user_id)
        lock_timeout = timeout or self.DEFAULT_LOCK_TIMEOUT
        return self.redis.lock(
            lock_key,
            timeout=lock_timeout,
            blocking=True,
            blocking_timeout=lock_timeout
        )
    
    async def clear_all_tokens(self) -> int:
        """
        Clear all cached tokens (useful for testing/maintenance).
        
        Returns:
            Number of keys deleted
        """
        try:
            pattern = f"{self.TOKEN_PREFIX}*"
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted_count += await self.redis.delete(*keys)
                if cursor == 0:
                    break
            
            logger.info(f"Cleared {deleted_count} tokens from cache")
            return deleted_count
        except Exception as e:
            logger.error(f"Error clearing tokens from Redis: {e}")
            return 0
    
    async def get_cache_stats(self) -> dict:
        """
        Get statistics about cached tokens.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            pattern = f"{self.TOKEN_PREFIX}*"
            cursor = 0
            token_count = 0
            
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)
                token_count += len(keys)
                if cursor == 0:
                    break
            
            info = await self.redis.info("memory")
            
            return {
                "cached_tokens": token_count,
                "redis_memory_used": info.get("used_memory_human", "N/A"),
                "redis_memory_peak": info.get("used_memory_peak_human", "N/A")
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}


def get_redis_token_cache(redis_client: redis.Redis) -> RedisTokenCache:
    """
    Factory function to create RedisTokenCache instance.
    Can be used as a FastAPI dependency.
    """
    return RedisTokenCache(redis_client)
