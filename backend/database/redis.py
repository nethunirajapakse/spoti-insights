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

    client = None
    try:
        pool = _get_pool()
        client = redis.Redis(connection_pool=pool)
        await client.ping()
        redis_breaker.record_success()
    except Exception as e:
        redis_breaker.record_failure()
        logger.warning(f"Redis unavailable: {e}")
        if client is not None:
            await client.aclose()
        yield None
        return
    
    try:
        yield client
    finally:
        await client.aclose()

async def ping_redis() -> bool:
    client = None
    try:
        if not redis_breaker.is_available():
            return False
        pool = _get_pool()
        client = redis.Redis(connection_pool=pool)
        await client.ping()
        return True
    except Exception:
        return False
    finally:
        if client is not None:
            await client.aclose()


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

    async def get_cache_stats(self, include_token_count: bool = False) -> dict:
        """Return Redis cache statistics.

        By default returns only memory info (fast, O(1)).
        Pass include_token_count=True to also count cached tokens via
        a full key scan (O(N)) — use only in non-latency-sensitive contexts.
        """
        if not self.redis:
            return {"status": "disconnected"}
        try:
            info = await self.redis.info("memory")
            stats: dict = {
                "status": "ok",
                "memory": info.get("used_memory_human"),
            }
            if include_token_count:
                token_count = 0
                async for _ in self.redis.scan_iter(f"{self.TOKEN_PREFIX}*"):
                    token_count += 1
                stats["cached_tokens"] = token_count
            return stats
        except Exception as e:
            return {"status": "error", "error": str(e)}

import time

_last_deny_warn: float = 0.0
_DENY_WARN_INTERVAL = 60.0
class JWTDenylist:
    """
    Stores revoked JWT IDs (jti claims) in Redis with a TTL matching the
    token's remaining lifetime.

    Keys:   jwt:deny:{jti}
    Value:  "1" (presence is all that matters)
    TTL:    set to the token's remaining seconds so Redis self-cleans —
            no background job needed.

    Fail-open policy: if Redis is unavailable, is_denied() returns False
    so a Redis outage does not lock all users out. Log the bypass so it
    is visible in monitoring.
    """

    DENY_PREFIX = "jwt:deny:"

    def __init__(self, redis_client: redis.Redis | None):
        self.redis = redis_client

    def _key(self, jti: str) -> str:
        return f"{self.DENY_PREFIX}{jti}"

    async def add(self, jti: str, ttl_seconds: int) -> bool:
        """
        Deny a jti for ttl_seconds.
        ttl_seconds should be the token's remaining lifetime so the key
        self-expires exactly when the token would have anyway.
        Clamps to 1 second minimum so we never set a key with ex=0.
        Returns True on success, False if Redis is unavailable.
        """
        if not self.redis:
            logger.warning("JWTDenylist.add: Redis unavailable — jti=%.8s not denylisted", jti)
            return False
        try:
            await self.redis.set(self._key(jti), "1", ex=max(1, ttl_seconds))
            return True
        except (ConnectionError, TimeoutError) as e:
            logger.warning("JWTDenylist.add failed (Redis error): %s", e)
            return False

    async def is_denied(self, jti: str) -> bool:
        """
        Returns True if the jti is on the denylist.
        Returns False (fail-open) if Redis is unavailable — logs the bypass.
        """
        global _last_deny_warn

        if not self.redis:
            # Fix #2: throttle — log at most once per minute during outage
            now = time.monotonic()
            if now - _last_deny_warn >= _DENY_WARN_INTERVAL:
                logger.warning(
                    "JWTDenylist.is_denied: Redis unavailable — failing open. "
                    "Revoked tokens may be accepted until Redis recovers."
                )
                _last_deny_warn = now
            return False
        try:
            return bool(await self.redis.exists(self._key(jti)))
        except (ConnectionError, TimeoutError) as e:
            now = time.monotonic()
            if now - _last_deny_warn >= _DENY_WARN_INTERVAL:
                logger.warning("JWTDenylist.is_denied failed (Redis error) — fail-open: %s", e)
                _last_deny_warn = now
            return False
