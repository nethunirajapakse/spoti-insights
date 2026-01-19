import redis.asyncio as redis
from backend.core.config import settings

pool = redis.ConnectionPool.from_url(
    settings.redis_url or "redis://localhost:6379/0", 
    decode_responses=True
)

async def get_redis():
    """Dependency for Redis connections."""
    client = redis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.close()
