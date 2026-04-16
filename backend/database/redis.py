import redis.asyncio as redis
from backend.core.config import settings
import logging
import re
import time
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)

class RedisCircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_available(self) -> bool:
        if self.state == "OPEN":
            if (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        return True

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.error("Redis Circuit Breaker TRIP! State: OPEN")

    def record_success(self):
        self.failures = 0
        self.state = "CLOSED"

redis_breaker = RedisCircuitBreaker()
_pool = None
_pool_initialization_error = None

def _get_pool():
    global _pool, _pool_initialization_error
    if _pool_initialization_error:
        raise _pool_initialization_error

    if _pool is None:
        if not settings.redis_url:
            _pool_initialization_error = RuntimeError("Redis is not configured. Please set the REDIS_URL environment variable.")
            raise _pool_initialization_error
        
        try:
            # Use settings values to satisfy tests
            _pool = redis.ConnectionPool.from_url(
                settings.redis_url.replace("localhost", "127.0.0.1"), 
                decode_responses=True,
                max_connections=getattr(settings, "redis_max_connections", 10),
                socket_connect_timeout=settings.redis_socket_connect_timeout,
                socket_keepalive=True,
                health_check_interval=getattr(settings, "redis_health_check_interval", 30)
            )
            logger.info("Redis connection pool initialized")
        except Exception as e:
            _pool_initialization_error = e
            raise
    return _pool

async def get_redis():
    if not redis_breaker.is_available():
        yield None
        return
    try:
        pool = _get_pool()
        client = redis.Redis(connection_pool=pool)
        await client.ping() 
        redis_breaker.record_success()
        try:
            yield client
        finally:
            await client.aclose()
    except Exception as e:
        redis_breaker.record_failure()
        logger.warning(f"Redis unavailable: {e}")
        yield None

async def ping_redis() -> bool:
    try:
        if not redis_breaker.is_available(): return False
        pool = _get_pool()
        client = redis.Redis(connection_pool=pool)
        await client.ping()
        return True
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
        if not user_id:
            raise ValueError("user_id cannot be empty")
        if not re.match(r'^[a-zA-Z0-9_-]+$', user_id):
            raise ValueError(f"user_id contains invalid characters: {user_id!r}")
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
        if self.redis is None:
            raise RuntimeError("Redis client is not initialized")
        return self.redis.lock(self._get_lock_key(user_id), timeout=timeout or self.DEFAULT_LOCK_TIMEOUT, blocking=True)

    async def get_cache_stats(self) -> dict:
        """Return basic statistics about cached tokens and Redis memory usage."""
        if not self.redis: return {"status": "disconnected"}
        try:
            token_count = 0
            async for _ in self.redis.scan_iter(f"{self.TOKEN_PREFIX}*"):
                token_count += 1
            info = await self.redis.info("memory")
            return {
                "status": "ok",
                "cached_tokens": token_count,
                "memory": info.get("used_memory_human"),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
