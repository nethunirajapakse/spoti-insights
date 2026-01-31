import redis.asyncio as redis
from backend.core.config import settings
import logging
import re
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)

_pool = None
_pool_initialization_error = None

def _get_pool():
    global _pool, _pool_initialization_error
    if _pool_initialization_error:
        raise _pool_initialization_error

    if _pool is None:
        if not settings.redis_url:
            _pool_initialization_error = RuntimeError("Redis is not configured.")
            raise _pool_initialization_error
        
        try:
            _pool = redis.ConnectionPool.from_url(
                settings.redis_url, 
                decode_responses=True,
                max_connections=settings.redis_max_connections,
                socket_connect_timeout=settings.redis_socket_connect_timeout,
                socket_keepalive=True,
                health_check_interval=settings.redis_health_check_interval
            )
            logger.info("Redis connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis pool: {e}")
            _pool_initialization_error = e
            raise e
    return _pool

async def get_redis():
    """Yields None if Redis is unavailable to allow graceful degradation."""
    try:
        pool = _get_pool()
        client = redis.Redis(connection_pool=pool)
        await client.ping() # Verify connectivity
        try:
            yield client
        finally:
            await client.aclose()
    except Exception as e:
        logger.warning(f"Redis unavailable, yielding None for fallback: {e}")
        yield None

async def ping_redis() -> bool:
    try:
        pool = _get_pool()
        client = redis.Redis(connection_pool=pool)
        try:
            await client.ping()
            return True
        finally:
            await client.aclose()
    except Exception:
        return False

class RedisTokenCache:
    TOKEN_PREFIX = "spotify:token:"
    LOCK_PREFIX = "spotify:lock:refresh:"
    DEFAULT_LOCK_TIMEOUT = 10
    TOKEN_BUFFER = 60
    
    def __init__(self, redis_client: redis.Redis | None):
        self.redis = redis_client
    
    def _sanitize_user_id(self, user_id: str) -> str:
        if not user_id or not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
            raise ValueError(f"invalid user_id: {user_id}")
        return user_id
    
    def _get_token_key(self, user_id: str) -> str:
        return f"{self.TOKEN_PREFIX}{self._sanitize_user_id(user_id)}"
    
    def _get_lock_key(self, user_id: str) -> str:
        return f"{self.LOCK_PREFIX}{self._sanitize_user_id(user_id)}"
    
    async def get_token(self, user_id: str) -> str | None:
        if not self.redis: return None
        try:
            return await self.redis.get(self._get_token_key(user_id))
        except (ConnectionError, TimeoutError):
            return None
    
    async def set_token(self, user_id: str, access_token: str, expires_in: int) -> bool:
        if not self.redis: return False
        try:
            ttl = max(1, expires_in - self.TOKEN_BUFFER)
            await self.redis.set(self._get_token_key(user_id), access_token, ex=ttl)
            return True
        except (ConnectionError, TimeoutError):
            return False
    
    async def invalidate_token(self, user_id: str) -> bool:
        if not self.redis: return False
        try:
            return bool(await self.redis.delete(self._get_token_key(user_id)))
        except (ConnectionError, TimeoutError):
            return False
    
    def get_refresh_lock(self, user_id: str, timeout: int | None = None):
        """Note: Always wrap the usage of this lock in a try/except for ConnectionError."""
        lock_timeout = timeout or self.DEFAULT_LOCK_TIMEOUT
        return self.redis.lock(
            self._get_lock_key(user_id),
            timeout=lock_timeout,
            blocking=True,
            blocking_timeout=lock_timeout
        )
    
    async def get_cache_stats(self) -> dict:
        if not self.redis: return {"status": "disconnected"}
        try:
            token_count = 0
            async for _ in self.redis.scan_iter(f"{self.TOKEN_PREFIX}*"):
                token_count += 1
            info = await self.redis.info("memory")
            return {"cached_tokens": token_count, "memory": info.get("used_memory_human")}
        except Exception as e:
            return {"error": str(e)}
