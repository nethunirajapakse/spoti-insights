"""
Testing utilities for Redis-based token cache.
Run with: pytest tests/test_redis_cache.py -v
"""
import pytest
import pytest_asyncio
import asyncio
import redis.asyncio as redis
from backend.database.redis import RedisTokenCache, ping_redis
import time
import os

# Test configuration
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL")
RUN_REDIS_TESTS = os.getenv("RUN_REDIS_TESTS") == "1"

pytestmark = pytest.mark.skipif(
    not RUN_REDIS_TESTS or not TEST_REDIS_URL,
    reason="Redis integration tests require RUN_REDIS_TESTS=1 and TEST_REDIS_URL to be set.",
)

@pytest_asyncio.fixture
async def redis_client():
    """Fixture for Redis client."""
    client = redis.Redis.from_url(TEST_REDIS_URL, decode_responses=True)
    existing_keys = {key async for key in client.scan_iter(match="*")}
    try:
        yield client
    finally:
        current_keys = {key async for key in client.scan_iter(match="*")}
        keys_to_delete = list(current_keys - existing_keys)
        if keys_to_delete:
            await client.delete(*keys_to_delete)
        await client.aclose()

@pytest_asyncio.fixture
async def token_cache(redis_client):
    """Fixture for RedisTokenCache."""
    return RedisTokenCache(redis_client)

class TestRedisConnection:
    """Test Redis connectivity."""
    
    @pytest.mark.asyncio
    async def test_ping_redis(self, redis_client):
        """Test basic Redis connectivity."""
        result = await redis_client.ping()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_ping_redis_function(self):
        """Test ping_redis utility function."""
        # Note: This will fail if Redis is not running
        result = await ping_redis()
        assert isinstance(result, bool)

class TestTokenCache:
    """Test RedisTokenCache functionality."""
    
    @pytest.mark.asyncio
    async def test_set_and_get_token(self, token_cache):
        """Test setting and retrieving a token."""
        user_id = "test_user_123"
        access_token = "test_access_token_abc"
        expires_in = 3600
        
        # Set token
        result = await token_cache.set_token(user_id, access_token, expires_in)
        assert result is True
        
        # Get token
        retrieved_token = await token_cache.get_token(user_id)
        assert retrieved_token == access_token
    
    @pytest.mark.asyncio
    async def test_token_expiration(self, token_cache):
        """Test that tokens expire correctly."""
        user_id = "test_user_expire"
        access_token = "short_lived_token"
        expires_in = 2  # 2 seconds
        
        # Set token with short TTL
        await token_cache.set_token(user_id, access_token, expires_in)
        
        # Token should exist immediately
        token = await token_cache.get_token(user_id)
        assert token == access_token
        
        # Wait for expiration
        await asyncio.sleep(3)
        
        # Token should be gone
        token = await token_cache.get_token(user_id)
        assert token is None
    
    @pytest.mark.asyncio
    async def test_token_buffer(self, token_cache, redis_client):
        """Test that token TTL includes safety buffer."""
        user_id = "test_user_buffer"
        access_token = "buffered_token"
        expires_in = 3600
        
        await token_cache.set_token(user_id, access_token, expires_in)
        
        # Check actual TTL in Redis
        token_key = token_cache._get_token_key(user_id)
        ttl = await redis_client.ttl(token_key)
        
        # TTL should be less than expires_in due to buffer
        expected_ttl = expires_in - token_cache.TOKEN_BUFFER
        assert ttl <= expected_ttl
        assert ttl > expected_ttl - 10  # Allow some variance
    
    @pytest.mark.asyncio
    async def test_invalidate_token(self, token_cache):
        """Test token invalidation."""
        user_id = "test_user_invalidate"
        access_token = "token_to_invalidate"
        
        # Set token
        await token_cache.set_token(user_id, access_token, 3600)
        assert await token_cache.get_token(user_id) == access_token
        
        # Invalidate
        result = await token_cache.invalidate_token(user_id)
        assert result is True
        
        # Token should be gone
        token = await token_cache.get_token(user_id)
        assert token is None
    
    @pytest.mark.asyncio
    async def test_nonexistent_token(self, token_cache):
        """Test retrieving non-existent token."""
        token = await token_cache.get_token("nonexistent_user")
        assert token is None
    
    @pytest.mark.asyncio
    async def test_multiple_users(self, token_cache):
        """Test caching tokens for multiple users."""
        users = [
            ("user_1", "token_1"),
            ("user_2", "token_2"),
            ("user_3", "token_3")
        ]
        
        # Set tokens for all users
        for user_id, token in users:
            await token_cache.set_token(user_id, token, 3600)
        
        # Verify all tokens
        for user_id, expected_token in users:
            retrieved_token = await token_cache.get_token(user_id)
            assert retrieved_token == expected_token

class TestDistributedLocking:
    """Test distributed locking mechanism."""
    
    @pytest.mark.asyncio
    async def test_lock_acquisition(self, token_cache):
        """Test basic lock acquisition and release."""
        user_id = "test_user_lock"
        
        async with token_cache.get_refresh_lock(user_id):
            # Inside lock
            pass
        
        # Lock should be released
        # Try acquiring again immediately
        async with token_cache.get_refresh_lock(user_id):
            pass
    
    @pytest.mark.asyncio
    async def test_concurrent_lock_blocking(self, token_cache):
        """Test that concurrent lock attempts block properly."""
        user_id = "test_user_concurrent"
        results = []
        
        async def acquire_lock(delay: float):
            async with token_cache.get_refresh_lock(user_id, timeout=5):
                results.append(f"acquired_{delay}")
                await asyncio.sleep(delay)
                results.append(f"released_{delay}")
        
        # Start two tasks that try to acquire the same lock
        task1 = asyncio.create_task(acquire_lock(0.5))
        task2 = asyncio.create_task(acquire_lock(0.5))
        
        await asyncio.gather(task1, task2)
        
        # Verify sequential execution: two acquire/release pairs
        assert len(results) == 4

        # First pair must be acquired_X then released_X with matching suffix
        assert results[0].startswith("acquired_")
        assert results[1].startswith("released_")
        assert results[0].split("_", 1)[1] == results[1].split("_", 1)[1]

        # Second pair must be acquired_Y then released_Y with matching suffix
        assert results[2].startswith("acquired_")
        assert results[3].startswith("released_")
        assert results[2].split("_", 1)[1] == results[3].split("_", 1)[1]


class TestCacheStatistics:
    """Test cache statistics and management."""
    
    @pytest.mark.asyncio
    async def test_get_cache_stats(self, token_cache):
        """Test cache statistics retrieval."""
        # Add some tokens
        for i in range(5):
            await token_cache.set_token(f"user_{i}", f"token_{i}", 3600)
        
        stats = await token_cache.get_cache_stats()
        
        assert "cached_tokens" in stats
        assert stats["cached_tokens"] == 5
        assert "memory" in stats


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_redis_connection_error(self):
        """Test behavior when Redis is unavailable."""
        # Create client with bad URL
        bad_client = redis.Redis.from_url(
            "redis://localhost:9999/0",  # Wrong port
            decode_responses=True,
            socket_connect_timeout=1
        )
        cache = RedisTokenCache(bad_client)
        
        # Operations should handle errors gracefully
        result = await cache.set_token("test", "token", 3600)
        assert result is False
        
        token = await cache.get_token("test")
        assert token is None
        
        await bad_client.aclose()
    
    @pytest.mark.asyncio
    async def test_minimum_ttl(self, token_cache):
        """Test that TTL never goes below 1 second."""
        user_id = "test_user_min_ttl"
        
        # Try to set with very short expiration
        await token_cache.set_token(user_id, "token", expires_in=10)
        
        # Should still work (minimum 1 second after buffer)
        token = await token_cache.get_token(user_id)
        assert token == "token"

class TestKeyGeneration:
    """Test Redis key generation."""
    
    @pytest.mark.asyncio
    async def test_token_key_format(self, token_cache):
        """Test token key format."""
        user_id = "test_user"
        key = token_cache._get_token_key(user_id)
        assert key == f"spotify:token:{user_id}"
    
    @pytest.mark.asyncio
    async def test_lock_key_format(self, token_cache):
        """Test lock key format."""
        user_id = "test_user"
        key = token_cache._get_lock_key(user_id)
        assert key == f"spotify:lock:refresh:{user_id}"
    
    @pytest.mark.asyncio
    async def test_user_id_with_hyphens(self, token_cache):
        """Test user_id with hyphens is allowed."""
        user_id = "test-user-123"
        key = token_cache._get_token_key(user_id)
        assert key == f"spotify:token:{user_id}"
    
    @pytest.mark.asyncio
    async def test_user_id_with_underscores(self, token_cache):
        """Test user_id with underscores is allowed."""
        user_id = "test_user_123"
        key = token_cache._get_token_key(user_id)
        assert key == f"spotify:token:{user_id}"
    
    @pytest.mark.asyncio
    async def test_user_id_alphanumeric(self, token_cache):
        """Test purely alphanumeric user_id is allowed."""
        user_id = "testuser123ABC"
        key = token_cache._get_token_key(user_id)
        assert key == f"spotify:token:{user_id}"
    
    @pytest.mark.asyncio
    async def test_user_id_with_colon_rejected(self, token_cache):
        """Test user_id with colon is rejected to prevent key collision."""
        user_id = "test:user"
        with pytest.raises(ValueError, match="invalid characters"):
            token_cache._get_token_key(user_id)
    
    @pytest.mark.asyncio
    async def test_user_id_with_newline_rejected(self, token_cache):
        """Test user_id with newline is rejected."""
        user_id = "test\nuser"
        with pytest.raises(ValueError, match="invalid characters"):
            token_cache._get_token_key(user_id)
    
    @pytest.mark.asyncio
    async def test_user_id_with_special_chars_rejected(self, token_cache):
        """Test user_id with special characters is rejected."""
        invalid_ids = [
            "test@user",
            "test user",  # space
            "test#user",
            "test$user",
            "test%user",
            "test/user",
            "test\\user",
            "test;user",
            "test|user",
        ]
        for user_id in invalid_ids:
            with pytest.raises(ValueError, match="invalid characters"):
                token_cache._get_token_key(user_id)
    
    @pytest.mark.asyncio
    async def test_empty_user_id_rejected(self, token_cache):
        """Test empty user_id is rejected."""
        with pytest.raises(ValueError, match="user_id cannot be empty"):
            token_cache._get_token_key("")
    
    @pytest.mark.asyncio
    async def test_sanitization_in_lock_key(self, token_cache):
        """Test that sanitization also applies to lock keys."""
        user_id = "test:user"
        with pytest.raises(ValueError, match="invalid characters"):
            token_cache._get_lock_key(user_id)

# Performance test (optional, can be slow)
@pytest.mark.slow
class TestPerformance:
    """Performance tests for cache operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_reads(self, token_cache):
        """Test concurrent read performance."""
        user_id = "perf_test_user"
        await token_cache.set_token(user_id, "test_token", 3600)
        
        # Concurrent reads
        tasks = [token_cache.get_token(user_id) for _ in range(100)]
        start = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start
        
        assert all(r == "test_token" for r in results)
        assert duration < 1.0  # Should complete in under 1 second
        print(f"100 concurrent reads completed in {duration:.3f}s")
    
    @pytest.mark.asyncio
    async def test_concurrent_writes(self, token_cache):
        """Test concurrent write performance."""
        tasks = [
            token_cache.set_token(f"user_{i}", f"token_{i}", 3600)
            for i in range(100)
        ]
        
        start = time.time()
        results = await asyncio.gather(*tasks)
        duration = time.time() - start
        
        assert all(results)
        assert duration < 2.0  # Should complete in under 2 seconds
        print(f"100 concurrent writes completed in {duration:.3f}s")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
