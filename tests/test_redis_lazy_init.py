"""
Test lazy initialization of Redis connection pool.
Run with: pytest tests/test_redis_lazy_init.py -v
"""
import pytest
import sys
from unittest.mock import patch, MagicMock
from backend.core.config import settings


def test_module_import_without_redis_url():
    """Test that the redis module can be imported even when Redis URL is None."""
    # This test verifies that importing the module doesn't fail at import time
    # when Redis is not configured
    
    # Save original redis_url
    original_url = settings.redis_url
    
    try:
        # Set redis_url to None to simulate missing configuration
        with patch.object(settings, 'redis_url', None):
            # Force reload the module to test import behavior
            if 'backend.database.redis' in sys.modules:
                del sys.modules['backend.database.redis']
            
            # This import should succeed even with redis_url=None
            from backend.database import redis as redis_module
            
            # Module should be imported successfully
            assert redis_module is not None
            assert hasattr(redis_module, 'get_redis')
            assert hasattr(redis_module, 'ping_redis')
            assert hasattr(redis_module, 'RedisTokenCache')
            
    finally:
        # Restore original settings
        settings.redis_url = original_url
        # Force reload to restore normal state
        if 'backend.database.redis' in sys.modules:
            del sys.modules['backend.database.redis']


def test_get_pool_raises_error_when_redis_url_is_none():
    """Test that _get_pool raises appropriate error when Redis URL is not configured."""
    # Force reload to ensure clean state
    if 'backend.database.redis' in sys.modules:
        del sys.modules['backend.database.redis']
    
    with patch.object(settings, 'redis_url', None):
        from backend.database.redis import _get_pool
        
        # Reset pool state to force reinitialization
        import backend.database.redis as redis_module
        redis_module._pool = None
        redis_module._pool_initialization_error = None
        
        with pytest.raises(RuntimeError) as exc_info:
            _get_pool()
        
        assert "Redis is not configured" in str(exc_info.value)
        assert "REDIS_URL" in str(exc_info.value)


def test_get_pool_caches_initialization_error():
    """Test that initialization errors are cached and reraised."""
    # Force reload to ensure clean state
    if 'backend.database.redis' in sys.modules:
        del sys.modules['backend.database.redis']
    
    with patch.object(settings, 'redis_url', None):
        from backend.database.redis import _get_pool
        
        # Reset pool state
        import backend.database.redis as redis_module
        redis_module._pool = None
        redis_module._pool_initialization_error = None
        
        # First call should fail and cache the error
        with pytest.raises(RuntimeError):
            _get_pool()
        
        # Second call should raise the same cached error
        with pytest.raises(RuntimeError) as exc_info:
            _get_pool()
        
        assert "Redis is not configured" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ping_redis_returns_false_when_not_configured():
    """Test that ping_redis returns False when Redis is not configured."""
    # Force reload to ensure clean state
    if 'backend.database.redis' in sys.modules:
        del sys.modules['backend.database.redis']
    
    with patch.object(settings, 'redis_url', None):
        from backend.database.redis import ping_redis
        
        # Reset pool state
        import backend.database.redis as redis_module
        redis_module._pool = None
        redis_module._pool_initialization_error = None
        
        # Should return False, not raise an exception
        result = await ping_redis()
        assert result is False


def test_get_pool_uses_settings_for_pool_configuration():
    """Test that _get_pool uses settings for pool configuration."""
    # Force reload to ensure clean state
    if 'backend.database.redis' in sys.modules:
        del sys.modules['backend.database.redis']
    
    test_url = "redis://test-host:6379/0"
    test_max_connections = 50
    test_timeout = 10
    test_health_interval = 60
    
    with patch.object(settings, 'redis_url', test_url), \
         patch.object(settings, 'redis_max_connections', test_max_connections), \
         patch.object(settings, 'redis_socket_connect_timeout', test_timeout), \
         patch.object(settings, 'redis_health_check_interval', test_health_interval), \
         patch('backend.database.redis.redis.ConnectionPool.from_url') as mock_from_url:
        
        # Mock the from_url to avoid actual connection
        mock_pool = MagicMock()
        mock_from_url.return_value = mock_pool
        
        from backend.database.redis import _get_pool
        
        # Reset pool state
        import backend.database.redis as redis_module
        redis_module._pool = None
        redis_module._pool_initialization_error = None
        
        # Call _get_pool
        pool = _get_pool()
        
        # Verify from_url was called with correct parameters
        mock_from_url.assert_called_once()
        call_args = mock_from_url.call_args
        
        assert call_args[0][0] == test_url
        assert call_args[1]['max_connections'] == test_max_connections
        assert call_args[1]['socket_connect_timeout'] == test_timeout
        assert call_args[1]['health_check_interval'] == test_health_interval
        assert call_args[1]['decode_responses'] is True
        assert call_args[1]['socket_keepalive'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
